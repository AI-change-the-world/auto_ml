// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'cv_resp.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

CvResp _$CvRespFromJson(Map<String, dynamic> json) =>
    CvResp(json['img_url'] as String, (json['point'] as num).toDouble())
      ..presignUrl = json['presignUrl'] as String?;

Map<String, dynamic> _$CvRespToJson(CvResp instance) => <String, dynamic>{
  'img_url': instance.imgUrl,
  'point': instance.score,
  'presignUrl': instance.presignUrl,
};
