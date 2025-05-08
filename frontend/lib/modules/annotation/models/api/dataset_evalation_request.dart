import 'package:json_annotation/json_annotation.dart';

part 'dataset_evalation_request.g.dart';

@JsonSerializable()
class DatasetEvalationRequest {
  final int datasetId;
  final int annotationId;

  DatasetEvalationRequest({
    required this.datasetId,
    required this.annotationId,
  });

  factory DatasetEvalationRequest.fromJson(Map<String, dynamic> json) =>
      _$DatasetEvalationRequestFromJson(json);

  Map<String, dynamic> toJson() => _$DatasetEvalationRequestToJson(this);
}
