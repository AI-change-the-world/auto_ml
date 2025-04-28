import 'package:json_annotation/json_annotation.dart';

part 'file_preview_request.g.dart';

@JsonSerializable()
class FilePreviewRequest {
  final String baseUrl;
  final int storageType;
  final String path;

  FilePreviewRequest({
    required this.baseUrl,
    required this.storageType,
    required this.path,
  });

  factory FilePreviewRequest.fromJson(Map<String, dynamic> json) =>
      _$FilePreviewRequestFromJson(json);

  Map<String, dynamic> toJson() => _$FilePreviewRequestToJson(this);
}
