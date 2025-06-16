// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'predict_single_image_request.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

PredictSingleImageRequest _$PredictSingleImageRequestFromJson(
  Map<String, dynamic> json,
) => PredictSingleImageRequest(
  modelId: (json['modelId'] as num).toInt(),
  data: json['data'] as String,
);

Map<String, dynamic> _$PredictSingleImageRequestToJson(
  PredictSingleImageRequest instance,
) => <String, dynamic>{'modelId': instance.modelId, 'data': instance.data};
