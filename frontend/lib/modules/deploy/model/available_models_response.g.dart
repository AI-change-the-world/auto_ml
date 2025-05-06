// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'available_models_response.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

AvailableModel _$AvailableModelFromJson(Map<String, dynamic> json) =>
    AvailableModel(
      id: (json['id'] as num).toInt(),
      savePath: json['savePath'] as String,
      baseModelName: json['baseModelName'] as String,
      loss: (json['loss'] as num).toDouble(),
      epoch: (json['epoch'] as num).toInt(),
      datasetId: (json['datasetId'] as num).toInt(),
      annotationId: (json['annotationId'] as num).toInt(),
      createdAt: DateTime.parse(json['createdAt'] as String),
      updatedAt: DateTime.parse(json['updatedAt'] as String),
    );

Map<String, dynamic> _$AvailableModelToJson(AvailableModel instance) =>
    <String, dynamic>{
      'id': instance.id,
      'savePath': instance.savePath,
      'baseModelName': instance.baseModelName,
      'loss': instance.loss,
      'epoch': instance.epoch,
      'datasetId': instance.datasetId,
      'annotationId': instance.annotationId,
      'createdAt': instance.createdAt.toIso8601String(),
      'updatedAt': instance.updatedAt.toIso8601String(),
    };
