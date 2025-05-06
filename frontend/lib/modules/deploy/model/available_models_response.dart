import 'package:json_annotation/json_annotation.dart';

part 'available_models_response.g.dart';

/*
{
        "id": 1,
        "savePath": "3f19d8b7-4a4e-4c82-8dc4-8b823dc44c57.pt",
        "baseModelName": "yolo11n.pt",
        "loss": 20.17616844177246,
        "epoch": 5,
        "datasetId": 5,
        "annotationId": 7,
        "createdAt": "2025-05-06T08:49:38",
        "updatedAt": "2025-05-06T08:49:38"
      }
*/

@JsonSerializable()
class AvailableModel {
  final int id;
  final String savePath;
  final String baseModelName;
  final double loss;
  final int epoch;
  final int datasetId;
  final int annotationId;
  final DateTime createdAt;
  final DateTime updatedAt;

  AvailableModel({
    required this.id,
    required this.savePath,
    required this.baseModelName,
    required this.loss,
    required this.epoch,
    required this.datasetId,
    required this.annotationId,
    required this.createdAt,
    required this.updatedAt,
  });

  factory AvailableModel.fromJson(Map<String, dynamic> json) =>
      _$AvailableModelFromJson(json);

  Map<String, dynamic> toJson() => _$AvailableModelToJson(this);
}
