import 'package:json_annotation/json_annotation.dart';

part 'sd_optimize_resp.g.dart';

@JsonSerializable()
class SdOptimizeResp {
  final String tip;
  final String img;

  String? presignUrl;

  SdOptimizeResp({required this.tip, required this.img});

  factory SdOptimizeResp.fromJson(Map<String, dynamic> json) =>
      _$SdOptimizeRespFromJson(json);

  Map<String, dynamic> toJson() => _$SdOptimizeRespToJson(this);
}
