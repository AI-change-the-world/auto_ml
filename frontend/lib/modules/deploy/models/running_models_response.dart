import 'package:json_annotation/json_annotation.dart';

part 'running_models_response.g.dart';

@JsonSerializable()
class RunningModelsResponse {
  @JsonKey(name: 'running_models')
  final List<int> runningModels;

  RunningModelsResponse({required this.runningModels});

  factory RunningModelsResponse.fromJson(Map<String, dynamic> json) =>
      _$RunningModelsResponseFromJson(json);

  Map<String, dynamic> toJson() => _$RunningModelsResponseToJson(this);
}
