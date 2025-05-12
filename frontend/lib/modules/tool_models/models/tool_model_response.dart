/*
{
      "id": 2,
      "name": "grounding dino",
      "description": "grounding dino",
      "type": "gd",
      "isEmbedded": 1,
      "createdAt": "2025-05-11T13:47:21",
      "updatedAt": "2025-05-11T13:47:21",
      "baseUrl": null,
      "apiKey": null,
      "modelName": "groundingdino_swint_ogc.pth"
    }
*/
import 'package:json_annotation/json_annotation.dart';

part 'tool_model_response.g.dart';

@JsonSerializable()
class ToolModelResponse {
  final List<ToolModel> toolModels;

  ToolModelResponse(this.toolModels);

  factory ToolModelResponse.fromJson(Map<String, dynamic> json) =>
      _$ToolModelResponseFromJson(json);

  Map<String, dynamic> toJson() => _$ToolModelResponseToJson(this);
}

@JsonSerializable()
class ToolModel {
  final int id;
  final String name;
  final String? description;
  final String? type;
  final int isEmbedded;
  final String createdAt;
  final String updatedAt;

  ToolModel({
    required this.id,
    required this.name,
    this.description,
    this.type,
    required this.isEmbedded,
    required this.createdAt,
    required this.updatedAt,
  });

  factory ToolModel.fromJson(Map<String, dynamic> json) =>
      _$ToolModelFromJson(json);

  Map<String, dynamic> toJson() => _$ToolModelToJson(this);
}
