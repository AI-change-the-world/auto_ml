// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'dataset_file_response.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

DatasetFileResponse _$DatasetFileResponseFromJson(Map<String, dynamic> json) =>
    DatasetFileResponse(
      datasetId: (json['datasetId'] as num).toInt(),
      count: (json['count'] as num).toInt(),
      files: (json['files'] as List<dynamic>).map((e) => e as String).toList(),
      datasetType: (json['datasetType'] as num).toInt(),
      storageType: (json['storageType'] as num).toInt(),
      datasetBaseUrl: json['datasetBaseUrl'] as String?,
    );

Map<String, dynamic> _$DatasetFileResponseToJson(
        DatasetFileResponse instance) =>
    <String, dynamic>{
      'datasetId': instance.datasetId,
      'count': instance.count,
      'files': instance.files,
      'datasetType': instance.datasetType,
      'storageType': instance.storageType,
      'datasetBaseUrl': instance.datasetBaseUrl,
    };
