import 'dart:math';

import 'package:auto_ml/api.dart';
import 'package:auto_ml/common/base_response.dart';
import 'package:auto_ml/modules/annotation/models/annotation.dart';
import 'package:auto_ml/modules/annotation/models/api/get_similar_object_request.dart';
import 'package:auto_ml/modules/annotation/models/api/update_annotation_request.dart';
import 'package:auto_ml/modules/annotation/models/changed.dart';
import 'package:auto_ml/modules/annotation/notifiers/annotation_state.dart';
import 'package:auto_ml/modules/annotation/notifiers/image_notifier.dart';
import 'package:auto_ml/modules/annotation/tools/label_to_annotation.dart';
import 'package:auto_ml/modules/current_dataset_annotation_notifier.dart';
import 'package:auto_ml/modules/predict/models/video_result.dart';
import 'package:auto_ml/utils/dio_instance.dart';
import 'package:auto_ml/utils/logger.dart';
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
      selectedAnnotationUuid: uuid,
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

  changeAnnotationVisibility(String uuid) {
    state = state.copyWith(
      annotations:
          state.annotations.map((e) {
            if (e.uuid == uuid) {
              return e.copyWith(visible: !e.visible);
            } else {
              return e;
            }
          }).toList(),
    );
  }

  changeAnnotationClassId(String uuid, int classId) {
    state = state.copyWith(
      modified: true,
      annotations:
          state.annotations.map((e) {
            if (e.uuid == uuid) {
              return e.copyWith(id: classId);
            } else {
              return e;
            }
          }).toList(),
    );
  }

  removeAnnotationById(String uuid) {
    state = state.copyWith(
      modified: true,
      annotations: List.of(state.annotations)
        ..retainWhere((v) => v.uuid != uuid),
    );
  }

  setAnnotations(String content) async {
    var imageState = ref.read(imageNotifierProvider);

    List<Annotation> annotations = parseYoloAnnotations(
      content,
      imageState.size.width,
      imageState.size.height,
    );

    logger.d("annotation length ${annotations.length}");

    state = state.copyWith(
      annotations: annotations,
      selectedAnnotationUuid: "",
    );
  }

  setAnnotationsWithClasses(String content) async {
    var imageState = ref.read(imageNotifierProvider);
    final classes = ref.read(currentDatasetAnnotationNotifierProvider).classes;

    List<Annotation> annotations = parseYoloAnnotationsWithClasses(
      content,
      imageState.size.width,
      imageState.size.height,
      classes,
    );

    logger.d("annotation length ${annotations.length}");

    state = state.copyWith(
      annotations: annotations,
      selectedAnnotationUuid: "",
    );
  }

  setAnnotationsInDetections(SingleImageResponse response) {
    StringBuffer sb = StringBuffer();
    final imgSize = ref.read(imageNotifierProvider).size;
    for (final i in response.results) {
      // print(i.toYoloFormat(imgSize));
      sb.write(i.toYoloFormat(imgSize));
      sb.write("\n");
    }
    state = state.copyWith(annotations: [], selectedAnnotationUuid: "");
    addAnnotation(sb.toString());
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
      modified: true,
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

  addAnnotation(String content) {
    var imageState = ref.read(imageNotifierProvider);
    final classes = ref.read(currentDatasetAnnotationNotifierProvider).classes;
    logger.d('Adding annotation: $content');
    logger.d("classes: $classes");
    List<Annotation> annotations = parseYoloAnnotations(
      content,
      imageState.size.width,
      imageState.size.height,
    );

    if (annotations.isNotEmpty) {
      state = state.copyWith(
        modified: true,
        annotations: [...state.annotations, ...annotations],
      );
    }
  }

  Future findSimilarAnnotation(List<String> classes) async {
    if (state.selectedAnnotationUuid.isEmpty) {
      return;
    }

    final currentAnnotation = state.annotations.firstWhere(
      (e) => e.uuid == state.selectedAnnotationUuid,
    );

    if (currentAnnotation.id == -1) {
      ToastUtils.error(null, title: "Annotaiton must have a valid label");
      return;
    }
    double left = currentAnnotation.position.dx;
    double top = currentAnnotation.position.dy;
    double right = left + currentAnnotation.width;
    double bottom = top + currentAnnotation.height;

    GetSimilarObjectRequest request = GetSimilarObjectRequest(
      left: left,
      top: top,
      right: right,
      bottom: bottom,
      path: ref.read(currentDatasetAnnotationNotifierProvider).currentData!.$1,
      label: currentAnnotation.getLabel(classes),
      id: ref.read(currentDatasetAnnotationNotifierProvider).annotationId,
    );

    DioClient().instance.post(Api.getSimilar, data: request.toJson()).then((v) {
      if (v.data != null) {
        final imgSize = ref.read(imageNotifierProvider).size;
        BaseResponse<SingleImageResponse> response =
            BaseResponse<SingleImageResponse>.fromJson(
              v.data,
              (j) => SingleImageResponse.fromJson(j as Map<String, dynamic>),
            );
        if (response.code == 200) {
          if (response.data != null) {
            StringBuffer sb = StringBuffer();
            for (final i in response.data!.results) {
              // print(i.toYoloFormat(imgSize));
              sb.write(i.toYoloFormat(imgSize));
              sb.write("\n");
            }
            addAnnotation(sb.toString());
          }
        } else {
          ToastUtils.error(null, title: "Find similar annotations failed");
        }
      } else {
        ToastUtils.error(null, title: "Server Error");
      }
    });
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
      modified: true,
      annotations:
          state.annotations.map((e) => e.copyWith(isOnAdding: false)).toList(),
    );
  }

  changeModifiedStatus(bool modified) {
    if (state.modified == modified) {
      return;
    }
    state = state.copyWith(modified: modified);
  }

  // TODO : support other formats
  Future<int> putYoloAnnotation() async {
    var imgSize = ref.read(imageNotifierProvider).size;
    var filename = "";
    String annotationSavePath =
        ref.read(currentDatasetAnnotationNotifierProvider).currentData?.$2 ??
        "";
    if (annotationSavePath.isEmpty) {
      filename =
          "${ref.read(currentDatasetAnnotationNotifierProvider).annotationPath}/${ref.read(currentDatasetAnnotationNotifierProvider).currentData?.$1.split("/").last.split(".").first}.txt";
    } else {
      filename = annotationSavePath;
    }

    var content = toYoloAnnotations(
      state.annotations,
      imgSize.width,
      imgSize.height,
    );
    UpdateAnnotationRequest request = UpdateAnnotationRequest(
      annotationPath: filename,
      content: content,
    );

    await DioClient().instance
        .post(Api.annotationUpdate, data: request.toJson())
        .then((v) {
          if (v.data == null) {
            ToastUtils.error(null, title: "Update annotation failed");
            return 1;
          }
          if (v.data!["code"] != 200) {
            ToastUtils.error(
              v.data!["message"],
              title: "Update annotation failed",
            );
            return 1;
          } else {
            ToastUtils.success(null, title: "Update annotation success");
          }
        });

    return 0;
  }
}

final annotationNotifierProvider =
    AutoDisposeNotifierProvider<AnnotationNotifier, AnnotationState>(
      AnnotationNotifier.new,
    );
