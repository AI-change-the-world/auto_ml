// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'get_all_dataset_response.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

Dataset _$DatasetFromJson(Map<String, dynamic> json) => Dataset(
      id: (json['id'] as num).toInt(),
      name: json['name'] as String,
      description: json['description'] as String,
      createdAt: DateTime.parse(json['createdAt'] as String),
      updatedAt: DateTime.parse(json['updatedAt'] as String),
      type: (json['type'] as num).toInt(),
      ranking: (json['ranking'] as num).toDouble(),
      storageType: (json['storageType'] as num).toInt(),
      url: json['url'] as String,
      username: json['username'] as String,
      password: json['password'] as String,
      scanStatus: (json['scanStatus'] as num).toInt(),
    );

Map<String, dynamic> _$DatasetToJson(Dataset instance) => <String, dynamic>{
      'id': instance.id,
      'name': instance.name,
      'description': instance.description,
      'createdAt': instance.createdAt.toIso8601String(),
      'updatedAt': instance.updatedAt.toIso8601String(),
      'type': instance.type,
      'ranking': instance.ranking,
      'storageType': instance.storageType,
      'url': instance.url,
      'username': instance.username,
      'password': instance.password,
      'scanStatus': instance.scanStatus,
    };

GetAllDatasetResponse _$GetAllDatasetResponseFromJson(
        Map<String, dynamic> json) =>
    GetAllDatasetResponse(
      datasets: (json['datasets'] as List<dynamic>)
          .map((e) => Dataset.fromJson(e as Map<String, dynamic>))
          .toList(),
    );

Map<String, dynamic> _$GetAllDatasetResponseToJson(
        GetAllDatasetResponse instance) =>
    <String, dynamic>{
      'datasets': instance.datasets,
    };
