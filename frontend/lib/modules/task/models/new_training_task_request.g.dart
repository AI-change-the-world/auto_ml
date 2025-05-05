// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'new_training_task_request.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

NewTrainingTaskRequest _$NewTrainingTaskRequestFromJson(
        Map<String, dynamic> json) =>
    NewTrainingTaskRequest(
      name: json['name'] as String,
      epoch: (json['epoch'] as num).toInt(),
      batch: (json['batch'] as num).toInt(),
      size: (json['size'] as num).toInt(),
      datasetId: (json['datasetId'] as num).toInt(),
      annotationId: (json['annotationId'] as num).toInt(),
      taskType: (json['taskType'] as num?)?.toInt() ?? 0,
    );

Map<String, dynamic> _$NewTrainingTaskRequestToJson(
        NewTrainingTaskRequest instance) =>
    <String, dynamic>{
      'name': instance.name,
      'epoch': instance.epoch,
      'batch': instance.batch,
      'size': instance.size,
      'datasetId': instance.datasetId,
      'annotationId': instance.annotationId,
      'taskType': instance.taskType,
    };
