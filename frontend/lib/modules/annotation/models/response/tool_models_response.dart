import 'package:json_annotation/json_annotation.dart';

part 'tool_models_response.g.dart';

@JsonSerializable()
class ToolModels {
  final List<ModelConfig> models;

  ToolModels({required this.models});

  factory ToolModels.fromJson(Map<String, dynamic> json) =>
      _$ToolModelsFromJson(json);

  Map<String, dynamic> toJson() => _$ToolModelsToJson(this);
}

@JsonSerializable()
class ModelConfig {
  final int id;
  final String name;
  final String description;
  final int type;
  final int isEmbedded;
  final DateTime createdAt;
  final DateTime updatedAt;
  final String baseUrl;
  final String apiKey;
  final String modelName;

  ModelConfig({
    required this.id,
    required this.name,
    required this.description,
    required this.type,
    required this.isEmbedded,
    required this.createdAt,
    required this.updatedAt,
    required this.baseUrl,
    required this.apiKey,
    required this.modelName,
  });

  factory ModelConfig.fromJson(Map<String, dynamic> json) =>
      _$ModelConfigFromJson(json);

  Map<String, dynamic> toJson() => _$ModelConfigToJson(this);
}
