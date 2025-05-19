// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'predict_cls_single_image_response.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

PredictClsSingleImageResponse _$PredictClsSingleImageResponseFromJson(
        Map<String, dynamic> json) =>
    PredictClsSingleImageResponse(
      imageId: json['image_id'] as String,
      name: json['name'] as String,
      confidence: (json['confidence'] as num).toDouble(),
      classId: (json['class_id'] as num).toInt(),
    );

Map<String, dynamic> _$PredictClsSingleImageResponseToJson(
        PredictClsSingleImageResponse instance) =>
    <String, dynamic>{
      'image_id': instance.imageId,
      'name': instance.name,
      'confidence': instance.confidence,
      'class_id': instance.classId,
    };
