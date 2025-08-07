import 'package:auto_ml/api.dart';
import 'package:auto_ml/common/base_response.dart';
import 'package:auto_ml/common/merge_files_and_annotations.dart';
import 'package:auto_ml/modules/annotation/models/api/annotation_file_response.dart';
import 'package:auto_ml/modules/annotation/models/api/dataset_file_response.dart';
import 'package:auto_ml/modules/annotation/notifiers/annotation_notifier.dart';
import 'package:auto_ml/modules/annotation/notifiers/enum.dart';
import 'package:auto_ml/modules/annotation/notifiers/image_notifier.dart';
import 'package:auto_ml/modules/dataset/models/file_preview_request.dart';
import 'package:auto_ml/modules/dataset/models/file_preview_response.dart';
import 'package:auto_ml/modules/dataset/models/get_all_dataset_response.dart';

import 'package:auto_ml/utils/dio_instance.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../utils/logger.dart';
import 'dataset/models/annotation_list_response.dart';

class CurrentDatasetAnnotationState {
  final Dataset? dataset;
  final Annotation? annotation;
  // final (String, String)? currentData;
  final bool isLoading;
  final List<String> classes;

  late List<(String, String)> data = [];

  CurrentDatasetAnnotationState({
    this.dataset,
    this.annotation,
    // this.currentData,
    this.isLoading = false,
    this.classes = const [],
  });

  CurrentDatasetAnnotationState copyWith({
    Dataset? dataset,
    Annotation? annotation,
    // (String, String)? currentData,
    bool? isLoading,
    List<(String, String)>? data,
    // String? currentFilePath,
    List<String>? classes,
  }) {
    final current = CurrentDatasetAnnotationState(
      dataset: dataset ?? this.dataset,
      annotation: annotation ?? this.annotation,
      // currentData: currentData ?? this.currentData,
      isLoading: isLoading ?? this.isLoading,
      classes: classes ?? this.classes,
    );
    current.data = data ?? this.data;
    return current;
  }
}

class CurrentDatasetAnnotationNotifier
    extends AutoDisposeNotifier<CurrentDatasetAnnotationState> {
  final dio = DioClient().instance;
  @override
  CurrentDatasetAnnotationState build() {
    return CurrentDatasetAnnotationState();
  }

  Future<void> changeDatasetAndAnnotation(
    Dataset? dataset,
    Annotation? annotation,
  ) async {
    if ((dataset == null && annotation == null) ||
        (dataset?.id == 0 && annotation?.id == 0)) {
      state = state.copyWith(
        dataset: dataset,
        annotation: annotation,
        // isLoading: false,
        // currentData: ("", ""),
        // currentFilePath: null,
      );
      return;
    }
    state = state.copyWith(isLoading: true);
    try {
      final response = await dio.get(
        Api.datasetFileList.replaceAll("{id}", dataset!.id.toString()),
      );
      final d = BaseResponse.fromJson(
        response.data,
        (json) => DatasetFileResponse.fromJson(json as Map<String, dynamic>),
      );

      final response2 = await dio.get(
        Api.annotationFileList.replaceAll("{id}", annotation!.id.toString()),
      );

      final a = BaseResponse.fromJson(
        response2.data,
        (json) => AnnotationFileResponse.fromJson(json as Map<String, dynamic>),
      );

      List<(String, String)> data = mergeFilesAndAnnotations(
        d.data?.files ?? [],
        a.data?.files ?? [],
      );

      state = state.copyWith(
        dataset: dataset,
        annotation: annotation,
        data: data,
        isLoading: false,
        classes: a.data?.classes ?? [],
      );
    } catch (e, s) {
      logger.e(e);
      logger.e(s);
      state = CurrentDatasetAnnotationState();
    }
  }

  void prevData() {
    final currentData = ref.read(currentAnnotatingDataNotifierProvider);
    if (currentData == null) return;
    int currentIndex = state.data.indexOf(currentData);
    if (currentIndex == 0) return;
    var prevData = state.data[currentIndex - 1];
    changeCurrentData(prevData);
  }

  void nextData() {
    final currentData = ref.read(currentAnnotatingDataNotifierProvider);
    if (currentData == null) return;
    int currentIndex = state.data.indexOf(currentData);
    if (currentIndex == state.data.length - 1) return;
    var nextData = state.data[currentIndex + 1];
    changeCurrentData(nextData);
  }

  Future changeCurrentData((String, String) data) async {
    if (state.annotation == null) {
      return;
    }
    // ref.read(annotationContainerProvider.notifier).changeMode(LabelMode.edit);
    if (state.annotation!.annotationType == 1) {
      return _changeCurrentDataForObjectDetection(data);
    } else if (state.annotation!.annotationType == 3) {
      return _changeCurrentDataForImageUnderstanding(data);
    } else if (state.annotation!.annotationType == 0) {
      return _changeCurrentDataForCls(data);
    }
  }

  Future<void> _changeCurrentDataForObjectDetection(
    (String, String) data,
  ) async {
    logger.d("dataset and annotation $data");

    try {
      // clear all annotations
      ref
          .read(annotationContainerProvider.notifier)
          .setAnnotations("", mode: LabelMode.edit);

      final request = FilePreviewRequest(
        baseUrl: state.dataset?.localS3StoragePath ?? "",
        storageType: state.dataset?.storageType ?? 0,
        path: data.$1,
      );
      final response = await dio.post(Api.preview, data: request.toJson());

      final r = BaseResponse.fromJson(
        response.data,
        (v) => FilePreviewResponse.fromJson(v as Map<String, dynamic>),
      );

      if (data.$2 == "") {
        // state = state.copyWith(currentData: data, currentFilePath: data.$1);
        ref.read(currentAnnotatingDataNotifierProvider.notifier).setData(data);

        ref
            .read(imageNotifierProvider.notifier)
            .loadImage(r.data?.content ?? "", data.$1)
            .then((_) {
              ref
                  .read(annotationContainerProvider.notifier)
                  .setAnnotations("", mode: LabelMode.edit);
            });
        return;
      }

      final request2 = FilePreviewRequest(
        baseUrl: state.annotation?.annotationSavePath ?? "",
        storageType: 1,
        path: data.$2,
      );

      final response2 = await dio.post(
        Api.annotationContent,
        data: request2.toJson(),
      );

      final r2 = BaseResponse.fromJson(
        response2.data,
        (v) => FilePreviewResponse.fromJson(v as Map<String, dynamic>),
      );

      // return r.data?.content;
      // state = state.copyWith(currentData: data, currentFilePath: data.$1);
      ref.read(currentAnnotatingDataNotifierProvider.notifier).setData(data);

      ref
          .read(imageNotifierProvider.notifier)
          .loadImage(r.data?.content ?? "", data.$1)
          .then((_) {
            ref
                .read(annotationContainerProvider.notifier)
                .setAnnotations(r2.data?.content ?? "", mode: LabelMode.edit);
          });
    } catch (e) {
      logger.e(e);
    }
  }

  Future<void> _changeCurrentDataForImageUnderstanding(
    (String, String) data,
  ) async {
    logger.d("dataset and annotation $data");
    // state = state.copyWith(currentData: data, currentFilePath: data.$1);
    ref.read(currentAnnotatingDataNotifierProvider.notifier).setData(data);
  }

  Future<void> _changeCurrentDataForCls((String, String) data) async {
    logger.d("dataset and annotation $data");
    // state = state.copyWith(currentData: data, currentFilePath: data.$1);
    ref.read(currentAnnotatingDataNotifierProvider.notifier).setData(data);
  }

  void addClassType(String className) {
    if (state.classes.contains(className)) {
      return;
    }
    state = state.copyWith(classes: [...state.classes, className]);
  }

  void updateDataAfterAnnotationUpdate() {
    // var filename = state.currentData?.$1;
    var filename = ref.read(currentAnnotatingDataNotifierProvider)?.$1;
    if (filename == null) {
      return;
    }
    var annotationName =
        "${state.annotation?.annotationSavePath}/${filename.split("/").last.split(".").first}.txt";
    state = state.copyWith(
      // currentData: (filename, annotationName),
      data:
          state.data.map((e) {
            if (e.$1 == filename) {
              return (filename, annotationName);
            }
            return e;
          }).toList(),
    );
  }
}

final currentDatasetAnnotationNotifierProvider = AutoDisposeNotifierProvider<
  CurrentDatasetAnnotationNotifier,
  CurrentDatasetAnnotationState
>(CurrentDatasetAnnotationNotifier.new);

class CurrentDataNotifier extends AutoDisposeNotifier<(String, String)?> {
  @override
  (String, String)? build() {
    return null;
  }

  void setData((String, String)? data) {
    if (data != state) {
      state = data;
    }
  }
}

final currentAnnotatingDataNotifierProvider =
    AutoDisposeNotifierProvider<CurrentDataNotifier, (String, String)?>(
      CurrentDataNotifier.new,
    );
