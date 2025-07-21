// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'sd_augment_req.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

SDAugmentReq _$SDAugmentReqFromJson(Map<String, dynamic> json) => SDAugmentReq(
  loraName: json['lora_name'] as String?,
  jobType: json['job_type'] as String,
  prompt: json['prompt'] as String,
  negativePrompt: json['negative_prompt'] as String?,
  width: (json['width'] as num?)?.toInt() ?? 1024,
  height: (json['height'] as num?)?.toInt() ?? 1024,
  steps: (json['steps'] as num?)?.toInt() ?? 30,
  guidanceScale: (json['guidance_scale'] as num?)?.toDouble() ?? 7.5,
  seed: (json['seed'] as num?)?.toInt() ?? 123,
  count: (json['count'] as num?)?.toInt() ?? 1,
  img: json['img'] as String?,
  mask: json['mask'] as String?,
  promptOptimize: json['prompt_optimize'] as bool? ?? true,
);

Map<String, dynamic> _$SDAugmentReqToJson(SDAugmentReq instance) =>
    <String, dynamic>{
      'job_type': instance.jobType,
      'lora_name': instance.loraName,
      'prompt': instance.prompt,
      'negative_prompt': instance.negativePrompt,
      'width': instance.width,
      'height': instance.height,
      'steps': instance.steps,
      'guidance_scale': instance.guidanceScale,
      'seed': instance.seed,
      'count': instance.count,
      'img': instance.img,
      'mask': instance.mask,
      'prompt_optimize': instance.promptOptimize,
    };
