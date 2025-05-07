import 'package:json_annotation/json_annotation.dart';

part 'predict_single_image_request.g.dart';

@JsonSerializable()
class PredictSingleImageRequest {
  final int modelId;
  final String data;

  PredictSingleImageRequest({required this.modelId, required this.data});

  factory PredictSingleImageRequest.fromJson(Map<String, dynamic> json) =>
      _$PredictSingleImageRequestFromJson(json);

  Map<String, dynamic> toJson() => _$PredictSingleImageRequestToJson(this);
}
