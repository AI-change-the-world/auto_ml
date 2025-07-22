// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'sd_deep_optimize_req.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

SdDeepOptimizeReq _$SdDeepOptimizeReqFromJson(Map<String, dynamic> json) =>
    SdDeepOptimizeReq(
      prompt: json['prompt'] as String,
      img: json['img'] as String,
      loopTimes: (json['loop_times'] as num?)?.toInt() ?? 5,
      modelId: (json['model_id'] as num?)?.toInt() ?? 3,
    );

Map<String, dynamic> _$SdDeepOptimizeReqToJson(SdDeepOptimizeReq instance) =>
    <String, dynamic>{
      'prompt': instance.prompt,
      'img': instance.img,
      'loop_times': instance.loopTimes,
      'model_id': instance.modelId,
    };
