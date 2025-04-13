import 'dart:async';

import 'package:auto_ml/modules/dataset/notifier/dataset_state.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class DatasetNotifier extends AutoDisposeAsyncNotifier<DatasetState> {
  @override
  FutureOr<DatasetState> build() async {
    return DatasetState(datasets: []);
  }

  addDataset(Dataset dataset) async {
    state = AsyncValue.data(
      DatasetState(datasets: [...state.value!.datasets, dataset]),
    );
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
    state = await AsyncValue.guard(() async {
      return DatasetState(
        datasets: [
          for (final d in state.value!.datasets)
            if (d.id != id) d,
        ],
      );
    });
  }
}

final datasetNotifierProvider =
    AutoDisposeAsyncNotifierProvider<DatasetNotifier, DatasetState>(
      DatasetNotifier.new,
    );
