import 'package:json_annotation/json_annotation.dart';

part 'task.g.dart';

@Deprecated("unused")
@JsonSerializable()
class TaskResponse {
  final List<Task> tasks;

  TaskResponse({required this.tasks});

  factory TaskResponse.fromJson(Map<String, dynamic> json) =>
      _$TaskResponseFromJson(json);

  Map<String, dynamic> toJson() => _$TaskResponseToJson(this);
}

@JsonSerializable()
class Task {
  int taskId;
  int taskType;
  int datasetId;
  int annotationId;
  String createdAt;
  String updatedAt;

  Task({
    required this.taskId,
    required this.taskType,
    required this.datasetId,
    required this.annotationId,
    required this.createdAt,
    required this.updatedAt,
  });

  factory Task.fromJson(Map<String, dynamic> json) => _$TaskFromJson(json);

  Map<String, dynamic> toJson() => _$TaskToJson(this);
}
