import 'package:json_annotation/json_annotation.dart';

part 'get_similar_object_request.g.dart';

@JsonSerializable()
class GetSimilarObjectRequest {
  final String path;
  final double left;
  final double top;
  final double right;
  final double bottom;
  final String label;
  // model id
  final int model;
  // annotation id
  final int id;

  GetSimilarObjectRequest({
    required this.path,
    required this.left,
    required this.top,
    required this.right,
    required this.bottom,
    required this.label,
    this.model = 1,
    required this.id,
  });

  factory GetSimilarObjectRequest.fromJson(Map<String, dynamic> json) =>
      _$GetSimilarObjectRequestFromJson(json);

  Map<String, dynamic> toJson() => _$GetSimilarObjectRequestToJson(this);
}
