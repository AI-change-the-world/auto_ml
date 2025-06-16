// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'home_index_response.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

TaskPerDay _$TaskPerDayFromJson(Map<String, dynamic> json) => TaskPerDay(
  date: json['date'] as String,
  taskCount: (json['taskCount'] as num).toInt(),
  taskDuration: (json['taskDuration'] as num).toInt(),
);

Map<String, dynamic> _$TaskPerDayToJson(TaskPerDay instance) =>
    <String, dynamic>{
      'date': instance.date,
      'taskCount': instance.taskCount,
      'taskDuration': instance.taskDuration,
    };

HomeIndexResponse _$HomeIndexResponseFromJson(Map<String, dynamic> json) =>
    HomeIndexResponse(
      datasetCount: (json['datasetCount'] as num).toInt(),
      annotationCount: (json['annotationCount'] as num).toInt(),
      taskCount: (json['taskCount'] as num).toInt(),
      taskErrorCount: (json['taskErrorCount'] as num).toInt(),
      taskPerDays:
          (json['taskPerDays'] as List<dynamic>)
              .map((e) => TaskPerDay.fromJson(e as Map<String, dynamic>))
              .toList(),
    );

Map<String, dynamic> _$HomeIndexResponseToJson(HomeIndexResponse instance) =>
    <String, dynamic>{
      'datasetCount': instance.datasetCount,
      'annotationCount': instance.annotationCount,
      'taskCount': instance.taskCount,
      'taskErrorCount': instance.taskErrorCount,
      'taskPerDays': instance.taskPerDays,
    };
