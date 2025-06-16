// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'agent_simple_response.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

AgentSimpleResponse _$AgentSimpleResponseFromJson(Map<String, dynamic> json) =>
    AgentSimpleResponse(
      data:
          (json['data'] as List<dynamic>)
              .map((e) => AgentSimple.fromJson(e as Map<String, dynamic>))
              .toList(),
    );

Map<String, dynamic> _$AgentSimpleResponseToJson(
  AgentSimpleResponse instance,
) => <String, dynamic>{'data': instance.data};

AgentSimple _$AgentSimpleFromJson(Map<String, dynamic> json) => AgentSimple(
  id: (json['id'] as num).toInt(),
  name: json['name'] as String,
  isRecommended: (json['isRecommended'] as num).toInt(),
);

Map<String, dynamic> _$AgentSimpleToJson(AgentSimple instance) =>
    <String, dynamic>{
      'id': instance.id,
      'name': instance.name,
      'isRecommended': instance.isRecommended,
    };
