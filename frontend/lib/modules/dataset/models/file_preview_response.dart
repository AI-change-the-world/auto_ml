import 'package:json_annotation/json_annotation.dart';

part 'file_preview_response.g.dart';

@JsonSerializable()
class FilePreviewResponse {
  String? content;

  FilePreviewResponse({this.content});

  factory FilePreviewResponse.fromJson(Map<String, dynamic> json) =>
      _$FilePreviewResponseFromJson(json);

  Map<String, dynamic> toJson() => _$FilePreviewResponseToJson(this);
}
