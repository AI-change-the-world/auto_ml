// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'tool_models_response.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

ToolModels _$ToolModelsFromJson(Map<String, dynamic> json) => ToolModels(
  models:
      (json['models'] as List<dynamic>)
          .map((e) => ModelConfig.fromJson(e as Map<String, dynamic>))
          .toList(),
);

Map<String, dynamic> _$ToolModelsToJson(ToolModels instance) =>
    <String, dynamic>{'models': instance.models};

ModelConfig _$ModelConfigFromJson(Map<String, dynamic> json) => ModelConfig(
  id: (json['id'] as num).toInt(),
  name: json['name'] as String,
  description: json['description'] as String,
  type: (json['type'] as num).toInt(),
  isEmbedded: (json['isEmbedded'] as num).toInt(),
  createdAt: DateTime.parse(json['createdAt'] as String),
  updatedAt: DateTime.parse(json['updatedAt'] as String),
  baseUrl: json['baseUrl'] as String,
  apiKey: json['apiKey'] as String,
  modelName: json['modelName'] as String,
);

Map<String, dynamic> _$ModelConfigToJson(ModelConfig instance) =>
    <String, dynamic>{
      'id': instance.id,
      'name': instance.name,
      'description': instance.description,
      'type': instance.type,
      'isEmbedded': instance.isEmbedded,
      'createdAt': instance.createdAt.toIso8601String(),
      'updatedAt': instance.updatedAt.toIso8601String(),
      'baseUrl': instance.baseUrl,
      'apiKey': instance.apiKey,
      'modelName': instance.modelName,
    };
