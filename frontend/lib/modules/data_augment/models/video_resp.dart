import 'package:json_annotation/json_annotation.dart';

part 'video_resp.g.dart';

@JsonSerializable()
class VideoResp {
  final String? frame;
  final String? text;
  @JsonKey(name: 'frame_index')
  final int? frameIndex;

  @JsonKey(name: 'segment_index')
  final int? segmentIndex;

  VideoResp({this.frame, this.text, this.frameIndex, this.segmentIndex});

  factory VideoResp.fromJson(Map<String, dynamic> json) =>
      _$VideoRespFromJson(json);

  Map<String, dynamic> toJson() => _$VideoRespToJson(this);
}
