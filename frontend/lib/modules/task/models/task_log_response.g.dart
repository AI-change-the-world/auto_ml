// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'task_log_response.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

TaskLogResponse _$TaskLogResponseFromJson(Map<String, dynamic> json) =>
    TaskLogResponse(
      logs:
          (json['logs'] as List<dynamic>)
              .map((e) => TaskLog.fromJson(e as Map<String, dynamic>))
              .toList(),
    );

Map<String, dynamic> _$TaskLogResponseToJson(TaskLogResponse instance) =>
    <String, dynamic>{'logs': instance.logs};

TaskLog _$TaskLogFromJson(Map<String, dynamic> json) => TaskLog(
  logContent: json['logContent'] as String?,
  taskId: (json['taskId'] as num).toInt(),
  createdAt: json['createdAt'] as String,
);

Map<String, dynamic> _$TaskLogToJson(TaskLog instance) => <String, dynamic>{
  'logContent': instance.logContent,
  'taskId': instance.taskId,
  'createdAt': instance.createdAt,
};
