import 'dart:async';

import 'package:auto_ml/common/base_response.dart';
import 'package:auto_ml/modules/dataset/api.dart';
import 'package:auto_ml/modules/dataset/entity/get_all_dataset_response.dart'
    as r;
import 'package:auto_ml/modules/dataset/entity/get_dataset_storage_response.dart';
import 'package:auto_ml/modules/dataset/entity/new_dataset_request.dart';
import 'package:auto_ml/modules/dataset/entity/new_dataset_response.dart';
import 'package:auto_ml/modules/dataset/notifier/dataset_state.dart';
import 'package:auto_ml/utils/dio_instance.dart';
import 'package:auto_ml/utils/logger.dart';
import 'package:auto_ml/utils/toast_utils.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class DatasetNotifier extends AutoDisposeAsyncNotifier<DatasetState> {
  final dio = DioClient().instance;

  @override
  FutureOr<DatasetState> build() async {
    final response = await dio.get(Api.getAllDatasets);
    try {
      final d = BaseResponse.fromJson(
        response.data,
        (json) => r.GetAllDatasetResponse.fromJson({"datasets": json}),
      );
      if (d.data != null) {
        return DatasetState(
          datasets:
              d.data!.datasets.map((e) => Dataset.fromDataset(e)).toList(),
        );
      }
      return DatasetState(datasets: []);
    } catch (e) {
      logger.e(e);
      ToastUtils.error(null, title: "Get dataset failed");
      return DatasetState(datasets: []);
    }
  }

  changeCurrent(Dataset? dataset) {
    state = AsyncData(state.value!.copyWith(current: dataset));
  }

  Future getDatasetStorage(Dataset dataset) async {
    try {
      final res = await dio.get(
        Api.getStorage.replaceAll("{id}", dataset.id.toString()),
      );
      final d = BaseResponse.fromJson(
        res.data,
        (json) =>
            GetDatasetStorageResponse.fromJson(json as Map<String, dynamic>),
      );
      if (d.data != null) {
        dataset.datasetPath = d.data!.url;
        dataset.labelPath = d.data!.url;
        dataset.storageType = d.data!.storageType;
        dataset.username = d.data!.username ?? "";
        dataset.password = d.data!.password ?? "";
      }
    } catch (e) {
      ToastUtils.error(null, title: "Get dataset storage failed");
      logger.e(e);
    }
  }

  addDataset(Dataset dataset) async {
    state = AsyncLoading();

    NewDatasetRequest request = NewDatasetRequest(
      name: dataset.name,
      description: dataset.description,
      storageType: dataset.storageType,
      ranking: dataset.ranking,
      url: dataset.datasetPath,
      username: dataset.username,
      password: dataset.password,
    );

    try {
      final response = await dio.post(
        Api.createDataset,
        data: request.toJson(),
      );

      // state = AsyncValue.data(dataset);
      final r = BaseResponse.fromJson(
        response.data,
        (v) => NewDatasetResponse.fromJson(v as Map<String, dynamic>),
      );

      if (r.code == 200) {
        dataset.id = r.data!.id;
        ToastUtils.info(null, title: "Add dataset success");
        state = AsyncValue.data(
          DatasetState(datasets: [...state.value!.datasets, dataset]),
        );
      } else {
        ToastUtils.error(
          null,
          title: "Add dataset failed",
          description: response.data["message"],
        );
      }
    } catch (e) {
      logger.e(e);
      ToastUtils.error(null, title: "Add dataset failed");
    }
  }

  updateDataset(Dataset dataset) async {
    state = AsyncValue.loading();

    state = await AsyncValue.guard(() async {
      return DatasetState(
        datasets: [
          for (final d in state.value!.datasets)
            if (d.id == dataset.id) dataset else d,
        ],
      );
    });
  }

  deleteDataset(int id) async {
    state = AsyncLoading();
    try {
      final r = await dio.get(
        Api.deleteDataset.replaceAll("{id}", id.toString()),
      );
      final d = BaseResponse.fromJson(r.data, (c) => null);

      if (d.code == 200) {
        state = await AsyncValue.guard(() async {
          return DatasetState(
            datasets: [
              for (final d in state.value!.datasets)
                if (d.id != id) d,
            ],
          );
        });
        ToastUtils.sucess(null, title: "Deleted successfully");
      } else {
        ToastUtils.error(null, title: "Failed to delete");
      }
    } catch (e) {
      ToastUtils.error(null, title: "Delete dataset failed");
      return;
    }
  }
}

final datasetNotifierProvider =
    AutoDisposeAsyncNotifierProvider<DatasetNotifier, DatasetState>(
      DatasetNotifier.new,
    );
