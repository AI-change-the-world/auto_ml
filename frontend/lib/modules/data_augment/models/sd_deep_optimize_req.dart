import 'package:json_annotation/json_annotation.dart';

part 'sd_deep_optimize_req.g.dart';

@JsonSerializable()
class SdDeepOptimizeReq {
  final String prompt;
  final String img;
  @JsonKey(name: "loop_times")
  final int loopTimes;
  @JsonKey(name: "model_id")
  final int modelId;

  SdDeepOptimizeReq({
    required this.prompt,
    required this.img,
    this.loopTimes = 5,
    this.modelId = 3,
  });

  factory SdDeepOptimizeReq.fromJson(Map<String, dynamic> json) =>
      _$SdDeepOptimizeReqFromJson(json);

  Map<String, dynamic> toJson() => _$SdDeepOptimizeReqToJson(this);
}
