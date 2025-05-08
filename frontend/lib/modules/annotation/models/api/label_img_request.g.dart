// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'label_img_request.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

LabelImgRequest _$LabelImgRequestFromJson(Map<String, dynamic> json) =>
    LabelImgRequest(
      imagePath: json['image_path'] as String,
      classes:
          (json['classes'] as List<dynamic>).map((e) => e as String).toList(),
    );

Map<String, dynamic> _$LabelImgRequestToJson(LabelImgRequest instance) =>
    <String, dynamic>{
      'image_path': instance.imagePath,
      'classes': instance.classes,
    };
