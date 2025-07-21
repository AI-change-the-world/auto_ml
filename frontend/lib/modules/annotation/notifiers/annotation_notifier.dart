import 'dart:async';
import 'dart:convert';
import 'dart:math';

import 'package:auto_ml/api.dart';
import 'package:auto_ml/common/aether_base_response.dart';
import 'package:auto_ml/common/base_response.dart';
import 'package:auto_ml/common/sse/sse.dart';
import 'package:auto_ml/modules/annotation/models/annotation.dart';
import 'package:auto_ml/modules/annotation/models/api/get_similar_object_request.dart';
import 'package:auto_ml/modules/annotation/models/api/update_annotation_request.dart';
import 'package:auto_ml/modules/annotation/models/changed.dart';
import 'package:auto_ml/modules/annotation/notifiers/annotation_state.dart';
import 'package:auto_ml/modules/annotation/notifiers/enum.dart';
import 'package:auto_ml/modules/annotation/notifiers/image_notifier.dart';
import 'package:auto_ml/modules/annotation/tools/label_to_annotation.dart';
import 'package:auto_ml/modules/current_dataset_annotation_notifier.dart';
import 'package:auto_ml/modules/predict/models/video_result.dart';
import 'package:auto_ml/utils/dio_instance.dart';
import 'package:auto_ml/utils/globals.dart';
import 'package:auto_ml/utils/logger.dart';
import 'package:auto_ml/utils/toast_utils.dart';
import 'package:file_selector/file_selector.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
// ignore: depend_on_referenced_packages
import 'package:collection/collection.dart';
import 'package:uuid/uuid.dart';

@Deprecated("[REASON] Deprecated because of windows performance issue")
class AnnotationNotifier extends AutoDisposeNotifier<AnnotationState> {
  final StreamController<String> ss = StreamController.broadcast();
  @override
  AnnotationState build() {
    ref.onDispose(() {
      ss.close();
    });
    return AnnotationState();
  }

  void changeMode(LabelMode mode) {
    if (mode != state.mode) {
      state = state.copyWith(mode: mode);
    }
  }

  void easyChangeMode() {
    state = state.copyWith(
      mode: state.mode == LabelMode.edit ? LabelMode.add : LabelMode.edit,
    );
    if (state.mode == LabelMode.edit) {
      ToastUtils.info(null, title: "switch to edit mode");
    } else {
      ToastUtils.info(null, title: "switch to add mode");
    }
  }

  void changeCurrentAnnotation(String uuid) {
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

  void changeAnnotationVisibility(String uuid) {
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

  void changeCurrentSelectedAnnotationVisibility() {
    state = state.copyWith(
      annotations:
          state.annotations.map((e) {
            if (e.uuid == state.selectedAnnotationUuid) {
              return e.copyWith(visible: !e.visible);
            } else {
              return e;
            }
          }).toList(),
    );
  }

  void deleteCurrentSelectedAnnotation() {
    state = state.copyWith(
      modified: true,
      selectedAnnotationUuid: null,
      annotations: List.of(state.annotations)
        ..removeWhere((v) => v.uuid == state.selectedAnnotationUuid),
    );
  }

  void changeAnnotationClassId(String uuid, int classId) {
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

  void removeAnnotationById(String uuid) {
    state = state.copyWith(
      modified: true,
      annotations: List.of(state.annotations)
        ..retainWhere((v) => v.uuid != uuid),
    );
  }

  Future<void> setAnnotations(String content) async {
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

  Future<void> setAnnotationsWithClasses(String content) async {
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

  void setAnnotationsInDetections(SingleImageResponse response) {
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

  void addAnnotationInDetections(SingleImageResponse response) {
    StringBuffer sb = StringBuffer();
    final imgSize = ref.read(imageNotifierProvider).size;
    for (final i in response.results) {
      // print(i.toYoloFormat(imgSize));
      sb.write(i.toYoloFormat(imgSize));
      sb.write("\n");
    }
    addAnnotation(sb.toString());
  }

  void updateAnnotation(
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

  void addAnnotation(String content) {
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
      id: ref.read(currentDatasetAnnotationNotifierProvider).annotation!.id,
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

  void addFakeAnnotation(Annotation annotation) {
    annotation.isOnAdding = true;
    if (state.annotations.isNotEmpty && state.annotations.last.isOnAdding) {
      state = state.copyWith(
        annotations: [...state.annotations..removeLast(), annotation],
      );
    } else {
      state = state.copyWith(annotations: [...state.annotations, annotation]);
    }
  }

  void fakeAnnotationFinalize() {
    state = state.copyWith(
      modified: true,
      annotations:
          state.annotations.map((e) => e.copyWith(isOnAdding: false)).toList(),
    );
  }

  void changeModifiedStatus(bool modified) {
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
          "${ref.read(currentDatasetAnnotationNotifierProvider).annotation?.annotationSavePath}/${ref.read(currentDatasetAnnotationNotifierProvider).currentData?.$1.split("/").last.split(".").first}.txt";
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

  void handleAgent(int id, {bool stream = false}) async {
    logger.d("handleAgent id $id");
    final filePath =
        ref.read(currentDatasetAnnotationNotifierProvider).currentData?.$1;
    if (filePath == null) {
      ToastUtils.error(null, title: "Please select a file");
      return;
    }
    final annotationId =
        ref.read(currentDatasetAnnotationNotifierProvider).annotation?.id;
    final classes = ref.read(currentDatasetAnnotationNotifierProvider).classes;
    Map<String, dynamic> data = {"stream": stream};
    if (!stream) {
      if (id == 1) {
        data.addAll({
          "annotationId": annotationId,
          "imgPath": filePath,
          "agentId": 1,
        });
      } else if (id == 2) {
        data.addAll({
          "annotationId": annotationId,
          "imgPath": filePath,
          "agentId": 2,
        });
      } else if (id == 4) {
        if (state.selectedAnnotationUuid.isEmpty) {
          ToastUtils.error(null, title: "Please select an annotation first");
          return;
        }

        final currentAnnotation = state.annotations.firstWhere(
          (e) => e.uuid == state.selectedAnnotationUuid,
        );

        // if (currentAnnotation.id == -1) {
        //   ToastUtils.error(null, title: "Annotaiton must have a valid label");
        //   return;
        // }

        double left = currentAnnotation.position.dx;
        double top = currentAnnotation.position.dy;
        double right = left + currentAnnotation.width;
        double bottom = top + currentAnnotation.height;

        data.addAll({
          "annotationId": annotationId,
          "imgPath": filePath,
          "agentId": 4,
          "label": currentAnnotation.getLabel(classes),
          "left": left,
          "top": top,
          "right": right,
          "bottom": bottom,
        });
      } else if (id == 3) {
        final XFile? file = await openFile(
          acceptedTypeGroups: [Globals.imageType],
        );
        if (file == null) return;

        String base64 = base64Encode(await file.readAsBytes());

        data.addAll({
          "annotationId": annotationId,
          "imgPath": filePath,
          "agentId": 3,
          "template_image": base64,
        });
      } else if (id == 5) {
        data.addAll({
          "annotationId": annotationId,
          "imgPath": filePath,
          "agentId": 5,
        });
      } else {
        // TODO: 获取所有agent的作用，当前只支持auto label
        ToastUtils.info(null, title: "Only support auto label");
        data.addAll({
          "annotationId": annotationId,
          "imgPath": filePath,
          "agentId": id,
        });
      }

      try {
        final response = await DioClient().instance.post(Api.agent, data: data);
        BaseResponse<AetherBaseResponse<SingleImageResponse>> bs =
            BaseResponse<AetherBaseResponse<SingleImageResponse>>.fromJson(
              response.data,
              (json) => AetherBaseResponse<SingleImageResponse>.fromJson(
                json as Map<String, dynamic>,
                (json) =>
                    SingleImageResponse.fromJson(json as Map<String, dynamic>),
              ),
            );

        // logger.i(bs.data?.output?.results);
        if (bs.data != null && bs.data?.output != null) {
          addAnnotationInDetections(bs.data!.output!);
          ToastUtils.success(null, title: "Task completed");
        } else {
          ToastUtils.info(null, title: "Nothing found");
        }
        return;
      } catch (e, s) {
        logger.e(e);
        logger.e(s);
        ToastUtils.error(null, title: "Error labeling");
      }
    } else {
      /// stream
      ss.stream.listen((v) {
        print(v);
      });

      if (id == 1) {
        data.addAll({
          "annotationId": annotationId,
          "imgPath": filePath,
          "agentId": 1,
        });
      }
      sse(Api.baseUrl + Api.agent, data, ss);
    }
  }
}

@Deprecated("[REASON] Deprecated because of windows performance issue")
final annotationNotifierProvider =
    AutoDisposeNotifierProvider<AnnotationNotifier, AnnotationState>(
      AnnotationNotifier.new,
    );

class AnnotationContainerNotifier
    extends AutoDisposeNotifier<RefactorAnnotationState> {
  final StreamController<String> ss = StreamController.broadcast();
  @override
  RefactorAnnotationState build() {
    ref.onDispose(() {
      ss.close();
    });
    return RefactorAnnotationState(
      annotations: [
        Annotation(Offset.zero, 100, 100, 0)..uuid = "1-2-3-4",
        Annotation(Offset(100, 100), 300, 300, 0)..uuid = "4-256-3-4",
      ],
    ); // 或加载已有数据
  }

  void changeMode(LabelMode mode) {
    if (mode != state.mode) {
      state = state.copyWith(mode: mode);
    }
  }

  void easyChangeMode() {
    state = state.copyWith(
      mode: state.mode == LabelMode.edit ? LabelMode.add : LabelMode.edit,
    );
    if (state.mode == LabelMode.edit) {
      ToastUtils.info(null, title: "switch to edit mode");
    } else {
      ToastUtils.info(null, title: "switch to add mode");
    }
  }

  void changeCurrentAnnotation(String uuid) {
    // ref.read(singleAnnotationProvider(uuid).notifier)
    final newAnnotations = state.annotations.map((value) {
      if (value.uuid == uuid) {
        return value.copyWith(selected: true);
      } else {
        return value.copyWith(selected: false);
      }
    });
    state = state.copyWith(annotations: newAnnotations.toList());
  }

  void changeAnnotationVisibility(String uuid) {
    final newAnnotations = state.annotations.map((value) {
      if (value.uuid == uuid) {
        return value.copyWith(visible: !value.visible);
      } else {
        return value;
      }
    });
    state = state.copyWith(annotations: newAnnotations.toList());
  }

  void changeCurrentSelectedAnnotationVisibility() {
    final newAnnotations = state.annotations.map((value) {
      if (value.selected) {
        return value.copyWith(visible: !value.visible);
      } else {
        return value;
      }
    });

    state = state.copyWith(annotations: newAnnotations.toList());
  }

  void deleteCurrentSelectedAnnotation() {
    final newAnnotations = List<Annotation>.from(
      state.annotations..removeWhere((v) => v.selected),
    );
    state = state.copyWith(annotations: newAnnotations);
  }

  void removeAnnotationById(String uuid) {
    final newAnnotations = List<Annotation>.from(
      state.annotations..removeWhere((v) => v.uuid == uuid),
    );

    state = state.copyWith(annotations: newAnnotations);
  }

  Future<void> setAnnotations(String content) async {
    var imageState = ref.read(imageNotifierProvider);

    List<Annotation> annotations = parseYoloAnnotations(
      content,
      imageState.size.width,
      imageState.size.height,
    );

    logger.d("annotation length ${annotations.length}");
    // final Map<String, Annotation> newMap = annotations.fold(
    //   {},
    //   (Map<String, Annotation> map, annotation) =>
    //       map..putIfAbsent(annotation.uuid, () => annotation),
    // );

    state = state.copyWith(annotations: annotations);
  }

  Future<void> setAnnotationsWithClasses(String content) async {
    var imageState = ref.read(imageNotifierProvider);
    final classes = ref.read(currentDatasetAnnotationNotifierProvider).classes;

    List<Annotation> annotations = parseYoloAnnotationsWithClasses(
      content,
      imageState.size.width,
      imageState.size.height,
      classes,
    );

    logger.d("annotation length ${annotations.length}");

    // final Map<String, Annotation> newMap = annotations.fold(
    //   {},
    //   (Map<String, Annotation> map, annotation) =>
    //       map..putIfAbsent(annotation.uuid, () => annotation),
    // );

    state = state.copyWith(annotations: annotations);
  }

  /// TODO
  void setAnnotationsInDetections(SingleImageResponse response) {}

  /// TODO
  void addAnnotationInDetections(SingleImageResponse response) {}

  void addAnnotation(String content) {
    var imageState = ref.read(imageNotifierProvider);
    final classes = ref.read(currentDatasetAnnotationNotifierProvider).classes;
    logger.d('Adding annotation: $content');
    logger.d("classes: $classes");
    List<Annotation> annotations = parseYoloAnnotations(
      content,
      imageState.size.width,
      imageState.size.height,
    );

    // final newMap = Map<String, Annotation>.from(state.annotationMap)..addAll(
    //   annotations.fold(
    //     {},
    //     (Map<String, Annotation> map, annotation) =>
    //         map..putIfAbsent(annotation.uuid, () => annotation),
    //   ),
    // );

    if (annotations.isNotEmpty) {
      state = state.copyWith(
        modified: true,
        annotations: [...state.annotations, ...annotations],
      );
    }
  }

  /// TODO
  Future findSimilarAnnotation(List<String> classes) async {}

  void addFakeAnnotation(Annotation annotation) {
    annotation.isOnAdding = true;
    if (state.annotations.isNotEmpty && state.annotations.last.isOnAdding) {
      state = state.copyWith(
        annotations: [...state.annotations..removeLast(), annotation],
      );
    } else {
      state = state.copyWith(annotations: [...state.annotations, annotation]);
    }
  }

  void update({required String uuid, required Annotation annotation}) {
    final newAnnotations =
        state.annotations.map((e) {
          if (e.uuid == uuid) {
            return annotation;
          }
          return e;
        }).toList();

    state = state.copyWith(modified: true, annotations: newAnnotations);
  }

  void fakeAnnotationFinalize() {
    final lastAnnotation = state.annotations.last;
    lastAnnotation.uuid = Uuid().v4();
    lastAnnotation.isOnAdding = false;
    final list = List.from(state.annotations)..removeLast();
    state = state.copyWith(
      modified: true,
      annotations: [...list, lastAnnotation],
    );
  }

  void changeModifiedStatus(bool modified) {
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
          "${ref.read(currentDatasetAnnotationNotifierProvider).annotation?.annotationSavePath}/${ref.read(currentDatasetAnnotationNotifierProvider).currentData?.$1.split("/").last.split(".").first}.txt";
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

  void handleAgent(int id, {bool stream = false}) async {
    logger.d("handleAgent id $id");
    final filePath =
        ref.read(currentDatasetAnnotationNotifierProvider).currentData?.$1;
    if (filePath == null) {
      ToastUtils.error(null, title: "Please select a file");
      return;
    }
    final annotationId =
        ref.read(currentDatasetAnnotationNotifierProvider).annotation?.id;
    final classes = ref.read(currentDatasetAnnotationNotifierProvider).classes;
    Map<String, dynamic> data = {"stream": stream};
    if (!stream) {
      if (id == 1) {
        data.addAll({
          "annotationId": annotationId,
          "imgPath": filePath,
          "agentId": 1,
        });
      } else if (id == 2) {
        data.addAll({
          "annotationId": annotationId,
          "imgPath": filePath,
          "agentId": 2,
        });
      } else if (id == 4) {
        final selected = state.annotations.firstWhereOrNull((v) => v.selected);

        if (selected == null) {
          ToastUtils.error(null, title: "Please select an annotation first");
          return;
        }

        final currentAnnotation = state.annotations.firstWhere(
          (e) => e.uuid == selected.uuid,
        );

        // if (currentAnnotation.id == -1) {
        //   ToastUtils.error(null, title: "Annotaiton must have a valid label");
        //   return;
        // }

        double left = currentAnnotation.position.dx;
        double top = currentAnnotation.position.dy;
        double right = left + currentAnnotation.width;
        double bottom = top + currentAnnotation.height;

        data.addAll({
          "annotationId": annotationId,
          "imgPath": filePath,
          "agentId": 4,
          "label": currentAnnotation.getLabel(classes),
          "left": left,
          "top": top,
          "right": right,
          "bottom": bottom,
        });
      } else if (id == 3) {
        final XFile? file = await openFile(
          acceptedTypeGroups: [Globals.imageType],
        );
        if (file == null) return;

        String base64 = base64Encode(await file.readAsBytes());

        data.addAll({
          "annotationId": annotationId,
          "imgPath": filePath,
          "agentId": 3,
          "template_image": base64,
        });
      } else if (id == 5) {
        data.addAll({
          "annotationId": annotationId,
          "imgPath": filePath,
          "agentId": 5,
        });
      } else {
        // TODO: 获取所有agent的作用，当前只支持auto label
        ToastUtils.info(null, title: "Only support auto label");
        data.addAll({
          "annotationId": annotationId,
          "imgPath": filePath,
          "agentId": id,
        });
      }

      try {
        final response = await DioClient().instance.post(Api.agent, data: data);
        BaseResponse<AetherBaseResponse<SingleImageResponse>> bs =
            BaseResponse<AetherBaseResponse<SingleImageResponse>>.fromJson(
              response.data,
              (json) => AetherBaseResponse<SingleImageResponse>.fromJson(
                json as Map<String, dynamic>,
                (json) =>
                    SingleImageResponse.fromJson(json as Map<String, dynamic>),
              ),
            );

        // logger.i(bs.data?.output?.results);
        if (bs.data != null && bs.data?.output != null) {
          addAnnotationInDetections(bs.data!.output!);
          ToastUtils.success(null, title: "Task completed");
        } else {
          ToastUtils.info(null, title: "Nothing found");
        }
        return;
      } catch (e, s) {
        logger.e(e);
        logger.e(s);
        ToastUtils.error(null, title: "Error labeling");
      }
    } else {
      /// stream
      ss.stream.listen((v) {
        print(v);
      });

      if (id == 1) {
        data.addAll({
          "annotationId": annotationId,
          "imgPath": filePath,
          "agentId": 1,
        });
      }
      sse(Api.baseUrl + Api.agent, data, ss);
    }
  }
}

final annotationContainerProvider = AutoDisposeNotifierProvider<
  AnnotationContainerNotifier,
  RefactorAnnotationState
>(() => AnnotationContainerNotifier());

class SingleAnnotationNotifier
    extends AutoDisposeFamilyNotifier<Annotation, String> {
  @override
  Annotation build(String uuid) {
    final container = ref.watch(annotationContainerProvider);
    final annotation = container.annotations.firstWhereOrNull(
      (v) => v.uuid == uuid,
    );
    if (annotation == null) {
      throw Exception('Annotation not found: $uuid');
    }
    return annotation;
  }

  void updateAnnotation({
    DragUpdateDetails? details,
    List<SizeChanged> sizeChanged = const [],
  }) {
    state = state.copyWith(
      position: state.position + (details?.delta ?? Offset.zero),
    );
    if (sizeChanged.isNotEmpty) {
      for (var changed in sizeChanged) {
        if (changed.type == SizeChangedType.left) {
          state = state.copyWith(
            position: Offset(
              state.position.dx + changed.value,
              state.position.dy,
            ),
            width: max(state.width - changed.value, 0),
          );
        }
        if (changed.type == SizeChangedType.top) {
          state = state.copyWith(
            position: Offset(
              state.position.dx,
              state.position.dy + changed.value,
            ),
            height: max(state.height - changed.value, 0),
          );
        }
        if (changed.type == SizeChangedType.right) {
          state = state.copyWith(width: state.width + changed.value);
        }
        if (changed.type == SizeChangedType.bottom) {
          state = state.copyWith(height: state.height + changed.value);
        }
      }
    }
    final container = ref.read(annotationContainerProvider.notifier);
    container.update(uuid: state.uuid, annotation: state);
  }

  void changeAnnotationClassId(int classId) {
    state = state.copyWith(id: classId);
    final container = ref.read(annotationContainerProvider.notifier);
    container.update(uuid: state.uuid, annotation: state);
  }
}

final singleAnnotationProvider = AutoDisposeNotifierProvider.family<
  SingleAnnotationNotifier,
  Annotation,
  String
>(SingleAnnotationNotifier.new);
