import 'package:json_annotation/json_annotation.dart';

part 'annotation_file_response.g.dart';

@JsonSerializable()
class AnnotationFileResponse {
  final int annotationId;
  final String annotationPath;
  final List<String> files;
  final List<String> classes;
  final int storageType;

  AnnotationFileResponse({
    required this.annotationId,
    required this.annotationPath,
    required this.files,
    required this.classes,
    required this.storageType,
  });

  factory AnnotationFileResponse.fromJson(Map<String, dynamic> json) =>
      _$AnnotationFileResponseFromJson(json);

  Map<String, dynamic> toJson() => _$AnnotationFileResponseToJson(this);
}
