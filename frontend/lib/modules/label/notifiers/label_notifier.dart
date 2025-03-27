import 'dart:io';
import 'dart:math';

import 'package:auto_ml/modules/label/models/annotation.dart';
import 'package:auto_ml/modules/label/models/changed.dart';
import 'package:auto_ml/modules/label/notifiers/label_state.dart';
import 'package:auto_ml/modules/label/tools/get_image_size.dart';
import 'package:auto_ml/modules/label/tools/label_to_annotation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class LabelNotifier
    extends AutoDisposeFamilyNotifier<LabelState, (String, String)> {
  @override
  LabelState build((String, String) arg) {
    return LabelState(dataPath: arg.$1, labelPath: arg.$2);
  }

  changeCurrentAnnotation(String uuid) {
    state = state.copyWith(
      currentLabels:
          state.currentLabels.map((e) {
            if (e.uuid == uuid) {
              return e.copyWith(selected: true);
            } else {
              return e.copyWith(selected: false);
            }
          }).toList(),
    );
  }

  updateAnnotation(
    Annotation annotation, {
    DragUpdateDetails? dragDetails,
    List<SizeChanged> sizeChanged = const [],
  }) {
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
      currentLabels:
          state.currentLabels
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

  void nextData() async {
    if (state.dataLabelPairs.isEmpty) {
      return;
    }

    if (state.dataLabelPairs.indexWhere((v) => v.key == state.current) ==
        state.dataLabelPairs.length - 1) {
      return;
    }

    String current = "";
    String label = "";
    List<Annotation> annotations = [];

    if (state.current == "") {
      // first data
      current = state.dataLabelPairs.first.key;
      label = state.dataLabelPairs.first.value;

      if (label != "") {
        Size imageSize = await getImageSizeAsync(FileImage(File(current)));
        annotations = parseYoloAnnotations(
          label,
          imageSize.width,
          imageSize.height,
        );
      }
      state = state.copyWith(current: current, currentLabels: annotations);
    } else {
      current =
          state
              .dataLabelPairs[state.dataLabelPairs.indexWhere(
                    (v) => v.key == state.current,
                  ) +
                  1]
              .key;
      label =
          state
              .dataLabelPairs[state.dataLabelPairs.indexWhere(
                    (v) => v.key == state.current,
                  ) +
                  1]
              .value;
      if (label != "") {
        Size imageSize = await getImageSizeAsync(FileImage(File(current)));
        annotations = parseYoloAnnotations(
          label,
          imageSize.width,
          imageSize.height,
        );
      }
      state = state.copyWith(current: current, currentLabels: annotations);
    }
  }
}

final labelNotifierProvider = AutoDisposeNotifierProvider.family<
  LabelNotifier,
  LabelState,
  (String, String)
>(LabelNotifier.new);
