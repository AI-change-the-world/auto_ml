import 'package:json_annotation/json_annotation.dart';

part 'dataset_file_response.g.dart';

@JsonSerializable()
class DatasetFileResponse {
  final int datasetId;
  final int count;
  final List<String> files;
  final int datasetType;
  final int storageType;
  final String datasetBaseUrl;

  DatasetFileResponse({
    required this.datasetId,
    required this.count,
    required this.files,
    required this.datasetType,
    required this.storageType,
    required this.datasetBaseUrl,
  });

  factory DatasetFileResponse.fromJson(Map<String, dynamic> json) =>
      _$DatasetFileResponseFromJson(json);

  Map<String, dynamic> toJson() => _$DatasetFileResponseToJson(this);
}
