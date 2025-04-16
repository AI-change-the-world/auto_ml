import 'package:json_annotation/json_annotation.dart';

part 'scan_result_response.g.dart';

@JsonSerializable()
class ScanResultResponse {
  final List<String> filePaths;
  final int status;
  final int count;

  ScanResultResponse({
    required this.filePaths,
    required this.status,
    required this.count,
  });

  factory ScanResultResponse.fromJson(Map<String, dynamic> json) =>
      _$ScanResultResponseFromJson(json);

  Map<String, dynamic> toJson() => _$ScanResultResponseToJson(this);

  @override
  String toString() {
    return 'ScanResultResponse{filePaths: $filePaths, status: $status, count: $count}';
  }
}
