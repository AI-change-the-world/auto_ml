import 'package:json_annotation/json_annotation.dart';

part 'base_model_response.g.dart';

@JsonSerializable()
class BaseModelResponse {
  final List<BaseModel> models;

  BaseModelResponse({required this.models});

  factory BaseModelResponse.fromJson(Map<String, dynamic> json) =>
      _$BaseModelResponseFromJson(json);

  Map<String, dynamic> toJson() => _$BaseModelResponseToJson(this);
}

/*
{
      "name": "yolov8n.pt",
      "id": 1,
      "createdAt": "2025-05-05T11:33:13",
      "updatedAt": "2025-05-05T11:34:25",
      "type": 1
    }
*/
@JsonSerializable()
class BaseModel {
  final int id;
  final String name;
  final String createdAt;
  final String updatedAt;
  final int type;

  BaseModel({
    required this.id,
    required this.name,
    required this.createdAt,
    required this.updatedAt,
    required this.type,
  });

  factory BaseModel.fromJson(Map<String, dynamic> json) =>
      _$BaseModelFromJson(json);

  Map<String, dynamic> toJson() => _$BaseModelToJson(this);
}
