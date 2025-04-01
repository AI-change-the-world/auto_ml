import 'dart:async';

import 'package:auto_ml/modules/dataset/notifier/dataset_state.dart';
import 'package:auto_ml/modules/isar/database.dart';
import 'package:auto_ml/modules/isar/dataset.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:isar/isar.dart';

class DatasetNotifier extends AutoDisposeAsyncNotifier<DatasetState> {
  final _isarDatabase = IsarDatabase();

  @override
  FutureOr<DatasetState> build() async {
    final datasets = await _isarDatabase.isar!.datasets.where().findAll();
    return DatasetState(datasets: datasets);
  }

  addDataset(Dataset dataset) async {
    final _ = await _isarDatabase.isar!.writeTxn(() async {
      return await _isarDatabase.isar!.datasets.put(dataset);
    });
    state = AsyncValue.data(
      DatasetState(datasets: [...state.value!.datasets, dataset]),
    );
  }

  updateDataset(Dataset dataset) async {
    state = AsyncValue.loading();

    state = await AsyncValue.guard(() async {
      final _ = await _isarDatabase.isar!.writeTxn(() async {
        return await _isarDatabase.isar!.datasets.put(dataset);
      });
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
      final _ = await _isarDatabase.isar!.writeTxn(() async {
        return await _isarDatabase.isar!.datasets.delete(id);
      });
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
