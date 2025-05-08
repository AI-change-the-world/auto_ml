import 'package:json_annotation/json_annotation.dart';

part 'update_annotation_request.g.dart';

@JsonSerializable()
class UpdateAnnotationRequest {
  final String annotationPath;
  final String content;

  UpdateAnnotationRequest({
    required this.annotationPath,
    required this.content,
  });

  factory UpdateAnnotationRequest.fromJson(Map<String, dynamic> json) =>
      _$UpdateAnnotationRequestFromJson(json);

  Map<String, dynamic> toJson() => _$UpdateAnnotationRequestToJson(this);
}
