// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'predict_list_response.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

PredictListResponse _$PredictListResponseFromJson(Map<String, dynamic> json) =>
    PredictListResponse(
      data: (json['data'] as List<dynamic>)
          .map((e) => PredictData.fromJson(e as Map<String, dynamic>))
          .toList(),
    );

Map<String, dynamic> _$PredictListResponseToJson(
        PredictListResponse instance) =>
    <String, dynamic>{
      'data': instance.data,
    };

PredictData _$PredictDataFromJson(Map<String, dynamic> json) => PredictData(
      id: (json['id'] as num).toInt(),
      storageType: (json['storageType'] as num).toInt(),
      dataType: (json['dataType'] as num).toInt(),
      url: json['url'] as String,
      fileName: json['fileName'] as String,
      createdAt: DateTime.parse(json['createdAt'] as String),
      updatedAt: DateTime.parse(json['updatedAt'] as String),
    );

Map<String, dynamic> _$PredictDataToJson(PredictData instance) =>
    <String, dynamic>{
      'id': instance.id,
      'storageType': instance.storageType,
      'dataType': instance.dataType,
      'url': instance.url,
      'fileName': instance.fileName,
      'createdAt': instance.createdAt.toIso8601String(),
      'updatedAt': instance.updatedAt.toIso8601String(),
    };
