import 'package:json_annotation/json_annotation.dart';

part 'get_all_dataset_response.g.dart';

@JsonSerializable()
class Dataset {
  final int id;
  final String name;
  final String description;
  final DateTime createdAt;
  final DateTime updatedAt;
  int type;
  final double ranking;
  final int storageType;
  String? url;
  String? username;
  String? password;
  final int scanStatus;
  final int fileCount;
  final String? sampleFilePath;
  final String? localS3StoragePath;

  Dataset({
    required this.id,
    required this.name,
    required this.description,
    required this.createdAt,
    required this.updatedAt,
    this.type = 0,
    required this.ranking,
    required this.storageType,
    this.url,
    this.username,
    this.password,
    required this.scanStatus,
    required this.fileCount,
    required this.sampleFilePath,
    required this.localS3StoragePath,
  });

  factory Dataset.fromJson(Map<String, dynamic> json) =>
      _$DatasetFromJson(json);

  Map<String, dynamic> toJson() => _$DatasetToJson(this);

  static Dataset fake() {
    return Dataset(
      id: 0,
      name: "",
      description: "",
      createdAt: DateTime.now(),
      updatedAt: DateTime.now(),
      ranking: 1,
      storageType: 1,
      scanStatus: 1,
      fileCount: 1,
      sampleFilePath: "",
      localS3StoragePath: "",
    );
  }
}

@JsonSerializable()
class GetAllDatasetResponse {
  final List<Dataset> datasets;

  GetAllDatasetResponse({required this.datasets});

  factory GetAllDatasetResponse.fromJson(Map<String, dynamic> json) =>
      _$GetAllDatasetResponseFromJson(json);

  Map<String, dynamic> toJson() => _$GetAllDatasetResponseToJson(this);
}
