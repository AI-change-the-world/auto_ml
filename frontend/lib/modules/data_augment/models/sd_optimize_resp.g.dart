// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'sd_optimize_resp.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

SdOptimizeResp _$SdOptimizeRespFromJson(Map<String, dynamic> json) =>
    SdOptimizeResp(tip: json['tip'] as String, img: json['img'] as String)
      ..presignUrl = json['presignUrl'] as String?;

Map<String, dynamic> _$SdOptimizeRespToJson(SdOptimizeResp instance) =>
    <String, dynamic>{
      'tip': instance.tip,
      'img': instance.img,
      'presignUrl': instance.presignUrl,
    };
