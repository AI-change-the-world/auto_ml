// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'task.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

TaskResponse _$TaskResponseFromJson(Map<String, dynamic> json) => TaskResponse(
      tasks: (json['tasks'] as List<dynamic>)
          .map((e) => Task.fromJson(e as Map<String, dynamic>))
          .toList(),
    );

Map<String, dynamic> _$TaskResponseToJson(TaskResponse instance) =>
    <String, dynamic>{
      'tasks': instance.tasks,
    };

Task _$TaskFromJson(Map<String, dynamic> json) => Task(
      taskId: (json['taskId'] as num).toInt(),
      taskType: (json['taskType'] as num).toInt(),
      datasetId: (json['datasetId'] as num).toInt(),
      annotationId: (json['annotationId'] as num).toInt(),
      createdAt: json['createdAt'] as String,
      updatedAt: json['updatedAt'] as String,
      status: (json['status'] as num).toInt(),
    );

Map<String, dynamic> _$TaskToJson(Task instance) => <String, dynamic>{
      'taskId': instance.taskId,
      'taskType': instance.taskType,
      'datasetId': instance.datasetId,
      'annotationId': instance.annotationId,
      'createdAt': instance.createdAt,
      'updatedAt': instance.updatedAt,
      'status': instance.status,
    };
