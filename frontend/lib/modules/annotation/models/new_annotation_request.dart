import 'package:json_annotation/json_annotation.dart';

part 'new_annotation_request.g.dart';

@JsonSerializable()
class NewAnnotationRequest {
  int datasetId;
  // 0:本地 1:s3 2:webdav ...
  int storageType;
  String? savePath;
  String? username;
  String? password;
  // 0:分类 1:检测 2:分割 3:其它
  int type;
  String classes;

  NewAnnotationRequest({
    required this.datasetId,
    required this.storageType,
    this.savePath,
    this.username,
    this.password,
    required this.type,
    required this.classes,
  });

  factory NewAnnotationRequest.fromJson(Map<String, dynamic> json) =>
      _$NewAnnotationRequestFromJson(json);

  Map<String, dynamic> toJson() => _$NewAnnotationRequestToJson(this);
}
