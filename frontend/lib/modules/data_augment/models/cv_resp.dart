import 'package:json_annotation/json_annotation.dart';

part 'cv_resp.g.dart';

@JsonSerializable()
class CvResp {
  @JsonKey(name: 'img_url')
  final String imgUrl;
  @JsonKey(name: 'point')
  final double score;
  String? presignUrl;

  CvResp(this.imgUrl, this.score);

  factory CvResp.fromJson(Map<String, dynamic> json) => _$CvRespFromJson(json);

  Map<String, dynamic> toJson() => _$CvRespToJson(this);
}
