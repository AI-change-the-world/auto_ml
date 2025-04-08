import 'dart:async';

import 'package:auto_ml/modules/isar/database.dart';
import 'package:auto_ml/modules/isar/model.dart';
import 'package:auto_ml/modules/models/notifier/model_state.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:isar/isar.dart';

class ModelNotifier extends AutoDisposeAsyncNotifier<ModelState> {
  final IsarDatabase isarDatabase = IsarDatabase();
  @override
  FutureOr<ModelState> build() async {
    final models = await isarDatabase.isar!.models.where().findAll();
    return ModelState(models: models);
  }
}

final modelNotifierProvider =
    AutoDisposeAsyncNotifierProvider<ModelNotifier, ModelState>(
      ModelNotifier.new,
    );
