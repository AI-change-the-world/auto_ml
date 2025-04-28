import 'package:json_annotation/json_annotation.dart';

part 'process_request.g.dart';

@JsonSerializable()
class ProcessRequest {
  final int fileId;

  /// reserved for future use
  final int methodId; // or agent id

  ProcessRequest({required this.fileId, this.methodId = -1});

  factory ProcessRequest.fromJson(Map<String, dynamic> json) =>
      _$ProcessRequestFromJson(json);

  Map<String, dynamic> toJson() => _$ProcessRequestToJson(this);
}
