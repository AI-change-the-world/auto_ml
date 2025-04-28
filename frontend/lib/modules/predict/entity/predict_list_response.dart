import 'package:json_annotation/json_annotation.dart';

part 'predict_list_response.g.dart';

@JsonSerializable()
class PredictListResponse {
  final List<PredictData> data;

  PredictListResponse({required this.data});

  factory PredictListResponse.fromJson(Map<String, dynamic> json) =>
      _$PredictListResponseFromJson(json);

  Map<String, dynamic> toJson() => _$PredictListResponseToJson(this);
}

@JsonSerializable()
class PredictData {
  final int id;
  final int storageType;
  final int dataType;
  final String url;
  final String fileName;
  final DateTime createdAt;
  final DateTime updatedAt;

  PredictData({
    required this.id,
    required this.storageType,
    required this.dataType,
    required this.url,
    required this.fileName,
    required this.createdAt,
    required this.updatedAt,
  });

  factory PredictData.fromJson(Map<String, dynamic> json) =>
      _$PredictDataFromJson(json);
  Map<String, dynamic> toJson() => _$PredictDataToJson(this);
}
