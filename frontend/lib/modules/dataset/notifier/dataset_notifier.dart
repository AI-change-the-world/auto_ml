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
    return DatasetState(datasets: datasets, selectedTypes: DatasetType.values);
  }

  updateSelectTypes(List<DatasetType> types) async {
    state = await AsyncValue.guard(() async {
      return state.value!.copyWith(selectedTypes: types);
    });
  }
}

final datasetNotifierProvider =
    AutoDisposeAsyncNotifierProvider<DatasetNotifier, DatasetState>(
      DatasetNotifier.new,
    );
