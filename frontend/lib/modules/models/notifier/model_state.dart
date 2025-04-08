import 'package:auto_ml/modules/isar/model.dart';

class ModelState {
  final List<Model> models;

  ModelState({required this.models});

  ModelState copyWith({List<Model>? models}) {
    return ModelState(models: models ?? this.models);
  }
}
