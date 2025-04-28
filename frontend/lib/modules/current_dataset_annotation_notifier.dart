import 'package:auto_ml/api.dart';
import 'package:auto_ml/common/base_response.dart';
import 'package:auto_ml/common/merge_files_and_annotations.dart';
import 'package:auto_ml/modules/annotation/models/response/annotation_file_response.dart';
import 'package:auto_ml/modules/annotation/models/response/dataset_file_response.dart';
import 'package:auto_ml/modules/annotation/notifiers/annotation_notifier.dart';
import 'package:auto_ml/modules/annotation/notifiers/image_notifier.dart';
import 'package:auto_ml/modules/dataset/models/file_preview_request.dart';
import 'package:auto_ml/modules/dataset/models/file_preview_response.dart';

import 'package:auto_ml/utils/dio_instance.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../utils/logger.dart';

class CurrentDatasetAnnotationState {
  final int datasetId;
  final int annotationId;

  final String datasetPath;
  final String annotationPath;
  final String currentData;
  final bool isLoading;
  final int datasetStorageType;
  final int annotationStorageType;
  final List<String> classes;

  late List<(String, String)> data = [];
  late String currentFilePath = "";

  CurrentDatasetAnnotationState({
    this.datasetId = 0,
    this.annotationId = 0,
    this.datasetPath = "",
    this.annotationPath = "",
    this.currentData = "",
    this.isLoading = false,
    this.datasetStorageType = 0,
    this.annotationStorageType = 0,
    this.classes = const [],
  });

  CurrentDatasetAnnotationState copyWith({
    int? datasetId,
    int? annotationId,
    String? datasetPath,
    String? annotationPath,
    @Deprecated("will be removed") String? currentData,
    bool? isLoading,
    int? datasetStorageType,
    List<(String, String)>? data,
    String? currentFilePath,
    int? annotationStorageType,
    List<String>? classes,
  }) {
    final current = CurrentDatasetAnnotationState(
      datasetId: datasetId ?? this.datasetId,
      annotationId: annotationId ?? this.annotationId,
      datasetPath: datasetPath ?? this.datasetPath,
      annotationPath: annotationPath ?? this.annotationPath,
      currentData: currentData ?? this.currentData,
      isLoading: isLoading ?? this.isLoading,
      datasetStorageType: datasetStorageType ?? this.datasetStorageType,
      annotationStorageType:
          annotationStorageType ?? this.annotationStorageType,
      classes: classes ?? this.classes,
    );
    current.data = data ?? this.data;
    current.currentFilePath = currentFilePath ?? this.currentFilePath;
    return current;
  }
}

class CurrentDatasetAnnotationNotifier
    extends Notifier<CurrentDatasetAnnotationState> {
  final dio = DioClient().instance;
  @override
  CurrentDatasetAnnotationState build() {
    return CurrentDatasetAnnotationState();
  }

  changeDatasetAndAnnotation(int datasetId, int annotationId) async {
    state = state.copyWith(isLoading: true);
    try {
      final response = await dio.get(
        Api.datasetFileList.replaceAll("{id}", datasetId.toString()),
      );
      final d = BaseResponse.fromJson(
        response.data,
        (json) => DatasetFileResponse.fromJson(json as Map<String, dynamic>),
      );

      final response2 = await dio.get(
        Api.annotationFileList.replaceAll("{id}", annotationId.toString()),
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
        datasetId: datasetId,
        annotationId: annotationId,
        datasetPath: d.data?.datasetBaseUrl ?? "",
        annotationPath: a.data?.annotationPath ?? "",
        data: data,
        datasetStorageType: d.data?.storageType ?? 0,
        annotationStorageType: a.data?.storageType ?? 0,
        isLoading: false,
        classes: a.data?.classes ?? [],
      );
    } catch (e) {
      state = CurrentDatasetAnnotationState();
    }
  }

  changeCurrentData((String, String) data) async {
    logger.d("dataset and annotation $data");
    if (state.datasetStorageType == 0) {
      try {
        final request = FilePreviewRequest(
          baseUrl: state.datasetPath,
          storageType: state.datasetStorageType,
          path: data.$1,
        );
        final response = await dio.post(
          Api.datasetContent,
          data: request.toJson(),
        );

        final r = BaseResponse.fromJson(
          response.data,
          (v) => FilePreviewResponse.fromJson(v as Map<String, dynamic>),
        );

        if (data.$2 == "") {
          state = state.copyWith(
            currentData: r.data?.content,
            currentFilePath: data.$1,
          );

          ref
              .read(imageNotifierProvider.notifier)
              .loadImage(r.data?.content ?? "", data.$1)
              .then((_) {
                ref
                    .read(annotationNotifierProvider.notifier)
                    .setAnnotations("");
              });
          return;
        }

        final request2 = FilePreviewRequest(
          baseUrl: state.annotationPath,
          storageType: state.annotationStorageType,
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
        state = state.copyWith(
          currentData: r.data?.content,
          currentFilePath: data.$1,
        );

        ref
            .read(imageNotifierProvider.notifier)
            .loadImage(r.data?.content ?? "", data.$1)
            .then((_) {
              ref
                  .read(annotationNotifierProvider.notifier)
                  .setAnnotations(r2.data?.content ?? "");
            });
      } catch (e) {
        logger.e(e);
      }
    }
  }

  addClassType(String className) {
    if (state.classes.contains(className)) {
      return;
    }
    state = state.copyWith(classes: [...state.classes, className]);
  }
}

final currentDatasetAnnotationNotifierProvider = NotifierProvider<
  CurrentDatasetAnnotationNotifier,
  CurrentDatasetAnnotationState
>(CurrentDatasetAnnotationNotifier.new);
