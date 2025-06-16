// {
//     "datasetCount": 6,
//     "annotationCount": 7,
//     "taskCount": 87,
//     "taskErrorCount": 0,
//     "taskPerDays": [
//       {
//         "date": "2025-06-10",
//         "taskCount": 0,
//         "taskDuration": 0
//       }
//     ]
//   }

import 'package:json_annotation/json_annotation.dart';

part 'home_index_response.g.dart';

@JsonSerializable()
class TaskPerDay {
  String date;
  int taskCount;
  int taskDuration;

  TaskPerDay({
    required this.date,
    required this.taskCount,
    required this.taskDuration,
  });

  factory TaskPerDay.fromJson(Map<String, dynamic> json) =>
      _$TaskPerDayFromJson(json);

  Map<String, dynamic> toJson() => _$TaskPerDayToJson(this);
}

@JsonSerializable()
class HomeIndexResponse {
  int datasetCount;
  int annotationCount;
  int taskCount;
  int taskErrorCount;
  List<TaskPerDay> taskPerDays;

  HomeIndexResponse({
    required this.datasetCount,
    required this.annotationCount,
    required this.taskCount,
    required this.taskErrorCount,
    required this.taskPerDays,
  });

  factory HomeIndexResponse.fromJson(Map<String, dynamic> json) =>
      _$HomeIndexResponseFromJson(json);

  Map<String, dynamic> toJson() => _$HomeIndexResponseToJson(this);
}
