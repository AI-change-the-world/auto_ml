/*
{
        "id": 1,
        "name": "自动标注",
        "description": "根据给定的类别，自动标注图形",
        "pipelineFilePath": null,
        "pipelineContent": null,
        "isEmbedded": 1,
        "updatedAt": "2025-05-10T08:48:03",
        "createdAt": "2025-05-10T08:48:03"
      }
*/

import 'package:json_annotation/json_annotation.dart';

part 'agent_response.g.dart';

@JsonSerializable()
class Agent {
  final int id;
  final String name;
  final String? description;
  final String? pipelineFilePath;
  final String? pipelineContent;
  final int isEmbedded;
  final String updatedAt;
  final String createdAt;
  final int isRecommended;

  Agent({
    required this.id,
    required this.name,
    required this.description,
    required this.pipelineFilePath,
    required this.pipelineContent,
    required this.isEmbedded,
    required this.updatedAt,
    required this.createdAt,
    required this.isRecommended,
  });

  factory Agent.fromJson(Map<String, dynamic> json) => _$AgentFromJson(json);

  Map<String, dynamic> toJson() => _$AgentToJson(this);
}
