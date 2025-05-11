// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'agent_response.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

Agent _$AgentFromJson(Map<String, dynamic> json) => Agent(
      id: (json['id'] as num).toInt(),
      name: json['name'] as String,
      description: json['description'] as String?,
      pipelineFilePath: json['pipelineFilePath'] as String?,
      pipelineContent: json['pipelineContent'] as String?,
      isEmbedded: (json['isEmbedded'] as num).toInt(),
      updatedAt: json['updatedAt'] as String,
      createdAt: json['createdAt'] as String,
      isRecommended: (json['isRecommended'] as num).toInt(),
    );

Map<String, dynamic> _$AgentToJson(Agent instance) => <String, dynamic>{
      'id': instance.id,
      'name': instance.name,
      'description': instance.description,
      'pipelineFilePath': instance.pipelineFilePath,
      'pipelineContent': instance.pipelineContent,
      'isEmbedded': instance.isEmbedded,
      'updatedAt': instance.updatedAt,
      'createdAt': instance.createdAt,
      'isRecommended': instance.isRecommended,
    };
