import 'dart:async';

import 'package:auto_ml/common/base_response.dart';
import 'package:auto_ml/modules/dataset/api.dart';
import 'package:auto_ml/modules/dataset/entity/file_preview_request.dart';
import 'package:auto_ml/modules/dataset/entity/file_preview_response.dart';
import 'package:auto_ml/modules/dataset/entity/scan_result_response.dart';
import 'package:auto_ml/modules/dataset/notifier/dataset_file_state.dart';
import 'package:auto_ml/modules/dataset/notifier/dataset_notifier.dart';
import 'package:auto_ml/modules/dataset/notifier/dataset_state.dart';
import 'package:auto_ml/utils/dio_instance.dart';
import 'package:auto_ml/utils/logger.dart';
import 'package:auto_ml/utils/toast_utils.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class DatasetFileListNotifier
    extends AutoDisposeAsyncNotifier<DatasetFileState> {
  final dio = DioClient().instance;

  @override
  FutureOr<DatasetFileState> build() {
    Future.microtask(() {
      final dataset = ref.read(datasetNotifierProvider).value?.current;
      if (dataset == null) {
        return;
      }
      init(dataset);
    });
    return DatasetFileState(files: [], count: 0, index: 0);
  }

  init(Dataset dataset) async {
    try {
      final response = await dio.get(
        Api.details.replaceAll("{id}", dataset.id.toString()),
      );
      final d = BaseResponse.fromJson(
        response.data,
        (json) => ScanResultResponse.fromJson(json as Map<String, dynamic>),
      );
      if (d.code == 200) {
        state = AsyncValue.data(
          DatasetFileState(
            files: d.data?.filePaths ?? [],
            count: d.data?.count ?? 0,
            index: 0,
            status: d.data?.status ?? 0,
          ),
        );
        final String? content = await getFileContent(
          dataset.datasetPath,
          dataset.storageType,
          0,
        );
        if (content != null) {
          state = AsyncValue.data(
            DatasetFileState(
              files: state.value!.files,
              count: state.value!.count,
              index: 0,
              currentContent: content,
              status: state.value!.status,
            ),
          );
        }
      } else {
        ToastUtils.error(
          null,
          title: "Get dataset failed",
          description: response.data["message"],
        );
      }
    } catch (e) {
      ToastUtils.error(null, title: "Get dataset failed");
    }
  }

  nextPage(String datasetBaseUrl, int storageType) async {
    if (state.value!.index == state.value!.files.length - 1) {
      return;
    }
    state = AsyncLoading();
    final String? content = await getFileContent(
      datasetBaseUrl,
      storageType,
      state.value!.index + 1,
    );
    if (content == null) {
      ToastUtils.error(null, title: "Get preview failed");
      return;
    }

    state = AsyncValue.data(
      DatasetFileState(
        files: state.value!.files,
        count: state.value!.count,
        index: state.value!.index + 1,
        currentContent: content,
        status: state.value!.status,
      ),
    );
  }

  previousPage(String datasetBaseUrl, int storageType) {
    // if (state.index > 0) {
    //   state = state.copyWith(index: state.index - 1);
    // }
  }

  Future<String?> getFileContent(
    String datasetBaseUrl,
    int storageType,
    int index,
  ) async {
    FilePreviewRequest request = FilePreviewRequest(
      baseUrl: datasetBaseUrl,
      storageType: storageType,
      path: state.value!.files[index],
    );
    try {
      logger.i(request.toJson());
      logger.i(dio.options.baseUrl + Api.preview);
      final response = await dio.post(Api.preview, data: request.toJson());

      final r = BaseResponse.fromJson(
        response.data,
        (v) => FilePreviewResponse.fromJson(v as Map<String, dynamic>),
      );

      return r.data?.content;
    } catch (e) {
      logger.e(e);
      return null;
    }
  }
}

final datasetFileListNotifierProvider =
    AutoDisposeAsyncNotifierProvider<DatasetFileListNotifier, DatasetFileState>(
      DatasetFileListNotifier.new,
    );
