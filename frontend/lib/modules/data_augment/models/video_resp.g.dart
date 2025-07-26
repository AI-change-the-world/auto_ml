// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'video_resp.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

VideoResp _$VideoRespFromJson(Map<String, dynamic> json) => VideoResp(
  frame: json['frame'] as String?,
  text: json['text'] as String?,
  frameIndex: (json['frame_index'] as num?)?.toInt(),
  segmentIndex: (json['segment_index'] as num?)?.toInt(),
);

Map<String, dynamic> _$VideoRespToJson(VideoResp instance) => <String, dynamic>{
  'frame': instance.frame,
  'text': instance.text,
  'frame_index': instance.frameIndex,
  'segment_index': instance.segmentIndex,
};
