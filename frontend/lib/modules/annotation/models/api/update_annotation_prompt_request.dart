import 'package:json_annotation/json_annotation.dart';

part 'update_annotation_prompt_request.g.dart';

@JsonSerializable()
class UpdateAnnotationPromptRequest {
  final String prompt;
  final int annotationId;

  UpdateAnnotationPromptRequest(this.prompt, this.annotationId);

  factory UpdateAnnotationPromptRequest.fromJson(Map<String, dynamic> json) =>
      _$UpdateAnnotationPromptRequestFromJson(json);

  Map<String, dynamic> toJson() => _$UpdateAnnotationPromptRequestToJson(this);
}
