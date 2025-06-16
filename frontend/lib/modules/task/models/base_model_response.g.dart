// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'base_model_response.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

BaseModelResponse _$BaseModelResponseFromJson(Map<String, dynamic> json) =>
    BaseModelResponse(
      models:
          (json['models'] as List<dynamic>)
              .map((e) => BaseModel.fromJson(e as Map<String, dynamic>))
              .toList(),
    );

Map<String, dynamic> _$BaseModelResponseToJson(BaseModelResponse instance) =>
    <String, dynamic>{'models': instance.models};

BaseModel _$BaseModelFromJson(Map<String, dynamic> json) => BaseModel(
  id: (json['id'] as num).toInt(),
  name: json['name'] as String,
  createdAt: json['createdAt'] as String,
  updatedAt: json['updatedAt'] as String,
  type: (json['type'] as num).toInt(),
);

Map<String, dynamic> _$BaseModelToJson(BaseModel instance) => <String, dynamic>{
  'id': instance.id,
  'name': instance.name,
  'createdAt': instance.createdAt,
  'updatedAt': instance.updatedAt,
  'type': instance.type,
};
