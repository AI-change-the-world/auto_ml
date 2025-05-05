import 'package:json_annotation/json_annotation.dart';

part 'new_training_task_request.g.dart';

@JsonSerializable()
class NewTrainingTaskRequest {
  final String name;
  final int epoch;
  final int batch;
  final int size;
  final int datasetId;
  final int annotationId;
  final int taskType;

  NewTrainingTaskRequest({
    required this.name,
    required this.epoch,
    required this.batch,
    required this.size,
    required this.datasetId,
    required this.annotationId,
    this.taskType = 0,
  });
  factory NewTrainingTaskRequest.fromJson(Map<String, dynamic> json) =>
      _$NewTrainingTaskRequestFromJson(json);

  Map<String, dynamic> toJson() => _$NewTrainingTaskRequestToJson(this);

  @override
  String toString() {
    return 'NewTrainingTaskRequest{name: $name, epoch: $epoch, batch: $batch, size: $size}';
  }
}
