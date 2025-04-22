import 'package:json_annotation/json_annotation.dart';

part 'auto_annotation_request.g.dart';

@JsonSerializable()
class AutoAnnotationRequest {
  // image saved path
  final String content;
  final String? prompt;
  final int modelId;
  final int annotationId;
  final int datasetId;
  final bool image;

  AutoAnnotationRequest({
    required this.content,
    this.prompt,
    required this.modelId,
    required this.annotationId,
    required this.datasetId,
    required this.image,
  });

  factory AutoAnnotationRequest.fromJson(Map<String, dynamic> json) =>
      _$AutoAnnotationRequestFromJson(json);

  Map<String, dynamic> toJson() => _$AutoAnnotationRequestToJson(this);
}
