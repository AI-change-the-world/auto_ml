import 'package:json_annotation/json_annotation.dart';

part 'task_log_response.g.dart';

@JsonSerializable()
class TaskLogResponse {
  List<TaskLog> logs;

  TaskLogResponse({required this.logs});

  factory TaskLogResponse.fromJson(Map<String, dynamic> json) =>
      _$TaskLogResponseFromJson(json);

  Map<String, dynamic> toJson() => _$TaskLogResponseToJson(this);
}

@JsonSerializable()
class TaskLog {
  String? logContent;
  int taskId;
  String createdAt;

  TaskLog({this.logContent, required this.taskId, required this.createdAt});

  factory TaskLog.fromJson(Map<String, dynamic> json) =>
      _$TaskLogFromJson(json);

  Map<String, dynamic> toJson() => _$TaskLogToJson(this);
}
