import 'package:json_annotation/json_annotation.dart';

part 'paginate_request.g.dart';

@JsonSerializable()
class PaginateRequest {
  int pageId;
  int pageSize;

  PaginateRequest({this.pageId = 1, this.pageSize = 10});

  factory PaginateRequest.fromJson(Map<String, dynamic> json) =>
      _$PaginateRequestFromJson(json);

  Map<String, dynamic> toJson() => _$PaginateRequestToJson(this);
}
