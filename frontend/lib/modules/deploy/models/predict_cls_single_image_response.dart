import 'package:json_annotation/json_annotation.dart';

part 'predict_cls_single_image_response.g.dart';

@JsonSerializable()
class PredictClsSingleImageResponse {
  @JsonKey(name: 'image_id')
  final String imageId;

  final String name;
  final double confidence;

  @JsonKey(name: 'class_id')
  final int classId;

  PredictClsSingleImageResponse({
    required this.imageId,
    required this.name,
    required this.confidence,
    required this.classId,
  });

  factory PredictClsSingleImageResponse.fromJson(Map<String, dynamic> json) =>
      _$PredictClsSingleImageResponseFromJson(json);

  Map<String, dynamic> toJson() => _$PredictClsSingleImageResponseToJson(this);
}
