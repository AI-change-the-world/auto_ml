import 'package:json_annotation/json_annotation.dart';

part 'update_annotation_request.g.dart';

@JsonSerializable()
class UpdateAnnotationRequest {
  final String content;
  final String annotationPath;

  UpdateAnnotationRequest({
    required this.content,
    required this.annotationPath,
  });

  factory UpdateAnnotationRequest.fromJson(Map<String, dynamic> json) =>
      _$UpdateAnnotationRequestFromJson(json);

  Map<String, dynamic> toJson() => _$UpdateAnnotationRequestToJson(this);
}
