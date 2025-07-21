// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'sd_initialize_req.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

SDInitializeRequest _$SDInitializeRequestFromJson(Map<String, dynamic> json) =>
    SDInitializeRequest(
      enableImg2img: json['enable_img2img'] as bool?,
      enableInpaint: json['enable_inpaint'] as bool?,
      modelPath: json['model_path'] as String?,
    );

Map<String, dynamic> _$SDInitializeRequestToJson(
  SDInitializeRequest instance,
) => <String, dynamic>{
  'enable_img2img': instance.enableImg2img,
  'enable_inpaint': instance.enableInpaint,
  'model_path': instance.modelPath,
};
