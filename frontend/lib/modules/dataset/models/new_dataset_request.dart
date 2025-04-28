import 'package:json_annotation/json_annotation.dart';

part 'new_dataset_request.g.dart';

@JsonSerializable()
class NewDatasetRequest {
  final String name;
  final String description;

  /// 0: 本地, 1: S3, 2: WebDAV ...
  final int storageType;

  final double ranking;
  final String url;
  final String? annotationUrl;
  final String? username;
  final String? password;

  NewDatasetRequest({
    required this.name,
    required this.description,
    required this.storageType,
    required this.ranking,
    required this.url,
    this.username,
    this.password,
    this.annotationUrl,
  });

  factory NewDatasetRequest.fromJson(Map<String, dynamic> json) =>
      _$NewDatasetRequestFromJson(json);

  Map<String, dynamic> toJson() => _$NewDatasetRequestToJson(this);
}
