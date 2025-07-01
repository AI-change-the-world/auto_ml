import 'dart:async';

import 'package:auto_ml/common/base_response.dart';
import 'package:auto_ml/api.dart';
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
    return DatasetFileState();
  }

  Future refresh(Dataset dataset) async {
    logger.i("refresh");
    init(dataset);
  }

  Future<void> init(Dataset dataset) async {
    try {
      final response = await dio.get(
        Api.details.replaceAll("{id}", dataset.id.toString()),
      );
      final d = BaseResponse.fromJson(
        response.data,
        (json) => DatasetFileState.fromJson(json as Map<String, dynamic>),
      );
      if (d.code == 200) {
        state = AsyncValue.data(
          DatasetFileState(
            samples: d.data?.samples ?? [],
            usedCount: d.data?.usedCount ?? 0,
          ),
        );
      } else {
        ToastUtils.error(
          null,
          title: "Get dataset failed",
          description: response.data["message"],
        );
      }
    } catch (e) {
      logger.e(e);
      ToastUtils.error(null, title: "Get dataset failed");
    }
  }
}

final datasetFileListNotifierProvider =
    AutoDisposeAsyncNotifierProvider<DatasetFileListNotifier, DatasetFileState>(
      DatasetFileListNotifier.new,
    );
