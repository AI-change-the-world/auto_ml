// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'tool_model_response.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

ToolModelResponse _$ToolModelResponseFromJson(Map<String, dynamic> json) =>
    ToolModelResponse(
      (json['toolModels'] as List<dynamic>)
          .map((e) => ToolModel.fromJson(e as Map<String, dynamic>))
          .toList(),
    );

Map<String, dynamic> _$ToolModelResponseToJson(ToolModelResponse instance) =>
    <String, dynamic>{'toolModels': instance.toolModels};

ToolModel _$ToolModelFromJson(Map<String, dynamic> json) => ToolModel(
  id: (json['id'] as num).toInt(),
  name: json['name'] as String,
  description: json['description'] as String?,
  type: json['type'] as String?,
  isEmbedded: (json['isEmbedded'] as num).toInt(),
  createdAt: json['createdAt'] as String,
  updatedAt: json['updatedAt'] as String,
);

Map<String, dynamic> _$ToolModelToJson(ToolModel instance) => <String, dynamic>{
  'id': instance.id,
  'name': instance.name,
  'description': instance.description,
  'type': instance.type,
  'isEmbedded': instance.isEmbedded,
  'createdAt': instance.createdAt,
  'updatedAt': instance.updatedAt,
};
