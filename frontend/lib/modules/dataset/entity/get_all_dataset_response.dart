import 'package:json_annotation/json_annotation.dart';

part 'get_all_dataset_response.g.dart';

@JsonSerializable()
@JsonSerializable()
class Dataset {
  final int id;
  final String name;
  final String description;
  final DateTime createdAt;
  final DateTime updatedAt;
  final int type;
  final double ranking;
  final int storageType;
  final String url;
  final String username;
  final String password;
  final int scanStatus;

  Dataset({
    required this.id,
    required this.name,
    required this.description,
    required this.createdAt,
    required this.updatedAt,
    required this.type,
    required this.ranking,
    required this.storageType,
    required this.url,
    required this.username,
    required this.password,
    required this.scanStatus,
  });

  factory Dataset.fromJson(Map<String, dynamic> json) =>
      _$DatasetFromJson(json);

  Map<String, dynamic> toJson() => _$DatasetToJson(this);
}

@JsonSerializable()
class GetAllDatasetResponse {
  final List<Dataset> datasets;

  GetAllDatasetResponse({required this.datasets});

  factory GetAllDatasetResponse.fromJson(Map<String, dynamic> json) =>
      _$GetAllDatasetResponseFromJson(json);

  Map<String, dynamic> toJson() => _$GetAllDatasetResponseToJson(this);
}
