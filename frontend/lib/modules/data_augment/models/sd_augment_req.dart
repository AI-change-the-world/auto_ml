// class SdAugmentRequest(BaseModel):
//     job_type: str  # [txt2img, img2img, inpaint]
//     lora_name: Optional[str] = None
//     prompt: str
//     negative_prompt: Optional[str] = None
//     width: int = 1024
//     height: int = 1024
//     steps: int = 30
//     guidance_scale: float = 7.5
//     seed: int = 123
//     count: int = 5
//     img: Optional[str] = None
//     mask: Optional[str] = None
//     # only for img to img augmentation
//     prompt_optimize: bool = False

import 'package:json_annotation/json_annotation.dart';

part 'sd_augment_req.g.dart';

@JsonSerializable()
class SDAugmentReq {
  @JsonKey(name: 'job_type')
  final String jobType;
  @JsonKey(name: 'lora_name')
  final String? loraName;

  final String prompt;
  @JsonKey(name: 'negative_prompt')
  final String? negativePrompt;

  final int width;
  final int height;
  final int steps;
  @JsonKey(name: 'guidance_scale')
  final double guidanceScale;

  final int seed;
  final int count;
  final String? img;
  final String? mask;
  @JsonKey(name: 'prompt_optimize')
  final bool promptOptimize;

  const SDAugmentReq({
    this.loraName,
    required this.jobType,
    required this.prompt,
    this.negativePrompt,
    this.width = 1024,
    this.height = 1024,
    this.steps = 30,
    this.guidanceScale = 7.5,
    this.seed = 123,
    this.count = 1,
    this.img,
    this.mask,
    this.promptOptimize = true,
  });

  factory SDAugmentReq.fromJson(Map<String, dynamic> json) =>
      _$SDAugmentReqFromJson(json);

  Map<String, dynamic> toJson() => _$SDAugmentReqToJson(this);
}
