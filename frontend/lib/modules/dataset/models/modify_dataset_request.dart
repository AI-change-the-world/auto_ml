import 'package:json_annotation/json_annotation.dart';

part 'modify_dataset_request.g.dart';

@JsonSerializable()
class ModifyDatasetRequest {
  final String name;
  final String description;

  /// 0: 本地, 1: S3, 2: WebDAV ...
  final int storageType;

  final double ranking;
  final String url;
  final String? username;
  final String? password;
  final int id;

  ModifyDatasetRequest({
    required this.name,
    required this.description,
    required this.storageType,
    required this.ranking,
    required this.url,
    this.username,
    this.password,
    required this.id,
  });

  factory ModifyDatasetRequest.fromJson(Map<String, dynamic> json) =>
      _$ModifyDatasetRequestFromJson(json);

  Map<String, dynamic> toJson() => _$ModifyDatasetRequestToJson(this);
}
