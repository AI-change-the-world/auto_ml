import 'package:auto_ml/modules/tool_models/models/tool_model_response.dart';

class ModelState {
  final List<ToolModel> models;

  ModelState({required this.models});

  ModelState copyWith({List<ToolModel>? models}) {
    return ModelState(models: models ?? this.models);
  }
}
