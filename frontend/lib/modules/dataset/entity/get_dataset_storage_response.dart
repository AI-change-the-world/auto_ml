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
  // 0: 正在扫描 1: 扫描完成 2: 扫描失败
  final int scanStatus;

  GetDatasetStorageResponse({
    required this.id,
    required this.storageType,
    required this.url,
    this.username,
    this.password,
    required this.updatedAt,
    required this.scanStatus,
  });

  factory GetDatasetStorageResponse.fromJson(Map<String, dynamic> json) =>
      _$GetDatasetStorageResponseFromJson(json);

  Map<String, dynamic> toJson() => _$GetDatasetStorageResponseToJson(this);
}
