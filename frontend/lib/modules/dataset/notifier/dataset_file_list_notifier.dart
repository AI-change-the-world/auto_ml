import 'dart:async';

import 'package:auto_ml/common/base_response.dart';
import 'package:auto_ml/api.dart';
import 'package:auto_ml/modules/dataset/models/file_preview_request.dart';
import 'package:auto_ml/modules/dataset/models/file_preview_response.dart';
import 'package:auto_ml/modules/dataset/models/get_all_dataset_response.dart'
    as ds;
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
    return DatasetFileState(count: 0);
  }

  Future refresh(Dataset dataset) async {
    logger.i("refresh");
    init(dataset);
  }

  init(Dataset dataset) async {
    try {
      final response = await dio.get(
        Api.details.replaceAll("{id}", dataset.id.toString()),
      );
      final d = BaseResponse.fromJson(
        response.data,
        (json) => ds.Dataset.fromJson(json as Map<String, dynamic>),
      );
      if (d.code == 200) {
        state = AsyncValue.data(
          DatasetFileState(
            sampleFile: d.data?.sampleFilePath,
            count: d.data?.fileCount ?? 0,
            status: d.data?.scanStatus ?? 0,
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
              sampleFile: d.data?.sampleFilePath,
              count: d.data?.fileCount ?? 0,
              status: d.data?.scanStatus ?? 0,
              currentContent: content,
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

  Future<String?> getFileContent(
    String datasetBaseUrl,
    int storageType,
    int index,
  ) async {
    FilePreviewRequest request = FilePreviewRequest(
      baseUrl: datasetBaseUrl,
      storageType: storageType,
      path: state.value?.sampleFile ?? "",
    );
    try {
      logger.d(request.toJson());
      logger.d(dio.options.baseUrl + Api.preview);
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
