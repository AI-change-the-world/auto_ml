import 'package:json_annotation/json_annotation.dart';

part 'new_tool_model_request.g.dart';

@JsonSerializable()
class NewToolModelRequest {
  String? baseUrl;
  String? apiKey;
  String? modelName;
  String? name;
  String? description;
  String? type;

  NewToolModelRequest({
    this.baseUrl,
    this.apiKey,
    this.modelName,
    this.name,
    this.description,
    this.type,
  });

  factory NewToolModelRequest.fromJson(Map<String, dynamic> json) =>
      _$NewToolModelRequestFromJson(json);

  Map<String, dynamic> toJson() => _$NewToolModelRequestToJson(this);
}
