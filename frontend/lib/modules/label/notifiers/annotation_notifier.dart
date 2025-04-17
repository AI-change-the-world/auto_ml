import 'dart:math';

import 'package:auto_ml/modules/label/models/annotation.dart';
import 'package:auto_ml/modules/label/models/changed.dart';
import 'package:auto_ml/modules/label/notifiers/annotation_state.dart';
import 'package:auto_ml/modules/label/notifiers/image_notifier.dart';
import 'package:auto_ml/modules/label/tools/label_to_annotation.dart';
import 'package:auto_ml/utils/toast_utils.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class AnnotationNotifier extends AutoDisposeNotifier<AnnotationState> {
  @override
  AnnotationState build() {
    return AnnotationState();
  }

  @Deprecated("use `easyChangeMode`")
  changeMode(LabelMode mode) {
    if (mode != state.mode) {
      state = state.copyWith(mode: mode);
    }
  }

  easyChangeMode() {
    state = state.copyWith(
      mode: state.mode == LabelMode.edit ? LabelMode.add : LabelMode.edit,
    );
    if (state.mode == LabelMode.edit) {
      ToastUtils.info(null, title: "switch to edit mode");
    } else {
      ToastUtils.info(null, title: "switch to add mode");
    }
  }

  changeCurrentAnnotation(String uuid) {
    state = state.copyWith(
      annotations:
          state.annotations.map((e) {
            if (e.uuid == uuid) {
              return e.copyWith(selected: true);
            } else {
              return e.copyWith(selected: false);
            }
          }).toList(),
    );
  }

  setAnnotations(
    String datasetPath,
    String labelPath,
    int datasetId,
    int annotationId,
  ) async {
    var imageState = ref.read(imageNotifierProvider(datasetPath)).value;

    while (imageState == null) {
      await Future.delayed(Duration(milliseconds: 100));
      imageState = ref.read(imageNotifierProvider(datasetPath)).value;
    }

    /// TODO: get annotaion

    /// FIXME: this is for test, remove later
    List<Annotation> annotations = parseYoloAnnotations(
      """
1 0.769437 0.377311 0.100000 0.100000
1 0.1 0.1 0.1 0.1
1 0.396125 0.554243 0.216410 0.161357
""",
      imageState.size.width,
      imageState.size.height,
    );

    state = state.copyWith(
      annotations: annotations,
      selectedAnnotationUuid: "",
    );
  }

  updateAnnotation(
    Annotation annotation, {
    DragUpdateDetails? dragDetails,
    List<SizeChanged> sizeChanged = const [],
  }) {
    if (state.mode == LabelMode.add) {
      return;
    }

    annotation = annotation.copyWith(
      position: annotation.position + (dragDetails?.delta ?? Offset.zero),
    );
    if (sizeChanged.isNotEmpty) {
      for (var changed in sizeChanged) {
        if (changed.type == SizeChangedType.left) {
          annotation.position = Offset(
            annotation.position.dx + changed.value,
            annotation.position.dy,
          );
          annotation.width = max(annotation.width - changed.value, 0);
        }
        if (changed.type == SizeChangedType.top) {
          annotation.position = Offset(
            annotation.position.dx,
            annotation.position.dy + changed.value,
          );
          annotation.height = max(annotation.height - changed.value, 0);
        }
        if (changed.type == SizeChangedType.right) {
          annotation.width = annotation.width + changed.value;
        }
        if (changed.type == SizeChangedType.bottom) {
          annotation.height = annotation.height + changed.value;
        }
      }
    }

    state = state.copyWith(
      annotations:
          state.annotations
              .map(
                (e) =>
                    e.uuid == annotation.uuid
                        ? annotation.copyWith(
                          position: annotation.position,
                          width: annotation.width,
                          height: annotation.height,
                        )
                        : e,
              )
              .toList(),
    );
  }

  addFakeAnnotation(Annotation annotation) {
    annotation.isOnAdding = true;
    if (state.annotations.isNotEmpty && state.annotations.last.isOnAdding) {
      state = state.copyWith(
        annotations: [...state.annotations..removeLast(), annotation],
      );
    } else {
      state = state.copyWith(annotations: [...state.annotations, annotation]);
    }
  }

  fakeAnnotationFinalize() {
    state = state.copyWith(
      annotations:
          state.annotations.map((e) => e.copyWith(isOnAdding: false)).toList(),
    );

    getYoloAnnotation();
  }

  /// FIXME
  getYoloAnnotation() async {
    var imageState = ref.read(imageNotifierProvider("assets/test.png")).value;

    while (imageState == null) {
      await Future.delayed(Duration(milliseconds: 100));
      imageState = ref.read(imageNotifierProvider("assets/test.png")).value;
    }

    print(
      toYoloAnnotations(
        state.annotations,
        imageState.size.width,
        imageState.size.height,
      ),
    );
  }
}

final annotationNotifierProvider =
    AutoDisposeNotifierProvider<AnnotationNotifier, AnnotationState>(
      AnnotationNotifier.new,
    );
