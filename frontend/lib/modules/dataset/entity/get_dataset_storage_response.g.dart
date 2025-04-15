// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'get_dataset_storage_response.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

GetDatasetStorageResponse _$GetDatasetStorageResponseFromJson(
        Map<String, dynamic> json) =>
    GetDatasetStorageResponse(
      id: (json['id'] as num).toInt(),
      storageType: (json['storageType'] as num).toInt(),
      url: json['url'] as String,
      username: json['username'] as String?,
      password: json['password'] as String?,
      updatedAt: DateTime.parse(json['updatedAt'] as String),
      scanStatus: (json['scanStatus'] as num).toInt(),
    );

Map<String, dynamic> _$GetDatasetStorageResponseToJson(
        GetDatasetStorageResponse instance) =>
    <String, dynamic>{
      'id': instance.id,
      'storageType': instance.storageType,
      'url': instance.url,
      'username': instance.username,
      'password': instance.password,
      'updatedAt': instance.updatedAt.toIso8601String(),
      'scanStatus': instance.scanStatus,
    };
