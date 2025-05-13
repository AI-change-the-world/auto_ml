import 'package:json_annotation/json_annotation.dart';

part 'annotation_list_response.g.dart';

@JsonSerializable()
class AnnotationListResponse {
  List<Annotation> annotations;

  AnnotationListResponse({required this.annotations});

  factory AnnotationListResponse.fromJson(Map<String, dynamic> json) =>
      _$AnnotationListResponseFromJson(json);

  Map<String, dynamic> toJson() => _$AnnotationListResponseToJson(this);
}

@JsonSerializable()
class Annotation {
  final int id;
  final int datasetId;
  // final int annotatedFileCount;
  final int annotationType;
  final DateTime updatedAt;
  final int isDeleted;
  final DateTime createdAt;
  final String? classItems;
  final String? annotationPath;
  final String? annotationSavePath;

  Annotation({
    required this.id,
    required this.datasetId,
    // required this.annotatedFileCount,
    required this.annotationType,
    required this.updatedAt,
    required this.isDeleted,
    required this.createdAt,
    this.classItems,
    this.annotationPath,
    this.annotationSavePath,
  });

  factory Annotation.fromJson(Map<String, dynamic> json) =>
      _$AnnotationFromJson(json);

  Map<String, dynamic> toJson() => _$AnnotationToJson(this);
}
