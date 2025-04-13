import 'package:json_annotation/json_annotation.dart';

part 'get_all_dataset_response.g.dart';

@JsonSerializable()
class Dataset {
  final int id;
  final String name;
  final String description;
  final DateTime createdAt;
  final DateTime updatedAt;
  final int type;
  final double ranking;

  Dataset({
    required this.id,
    required this.name,
    required this.description,
    required this.createdAt,
    required this.updatedAt,
    required this.type,
    required this.ranking,
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
