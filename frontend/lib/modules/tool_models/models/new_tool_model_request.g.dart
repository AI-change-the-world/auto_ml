// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'new_tool_model_request.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

NewToolModelRequest _$NewToolModelRequestFromJson(Map<String, dynamic> json) =>
    NewToolModelRequest(
      baseUrl: json['baseUrl'] as String?,
      apiKey: json['apiKey'] as String?,
      modelName: json['modelName'] as String?,
      name: json['name'] as String?,
      description: json['description'] as String?,
      type: json['type'] as String?,
    );

Map<String, dynamic> _$NewToolModelRequestToJson(
  NewToolModelRequest instance,
) => <String, dynamic>{
  'baseUrl': instance.baseUrl,
  'apiKey': instance.apiKey,
  'modelName': instance.modelName,
  'name': instance.name,
  'description': instance.description,
  'type': instance.type,
};
