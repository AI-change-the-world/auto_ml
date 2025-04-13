import 'package:json_annotation/json_annotation.dart';

part 'get_dataset_storage_response.g.dart';

@JsonSerializable()
class GetDatasetStorageResponse {
  final int id;
  final int storageType;
  final String url;
  final String? username;
  final String? password;
  final DateTime updatedAt;

  GetDatasetStorageResponse({
    required this.id,
    required this.storageType,
    required this.url,
    this.username,
    this.password,
    required this.updatedAt,
  });

  factory GetDatasetStorageResponse.fromJson(Map<String, dynamic> json) =>
      _$GetDatasetStorageResponseFromJson(json);

  Map<String, dynamic> toJson() => _$GetDatasetStorageResponseToJson(this);
}
