import 'package:auto_ml/modules/dataset/constants.dart';

class ModelState {
  final List<Model> models;

  ModelState({required this.models});

  ModelState copyWith({List<Model>? models}) {
    return ModelState(models: models ?? this.models);
  }
}

class Model {
  int? id;
  String? name;
  String? description;

  ModelType modelType = ModelType.vision;

  int createAt = DateTime.now().millisecondsSinceEpoch;

  String? baseUrl;
  String? apiKey;
  String? modelName;
}
