// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'auto_annotation_request.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

AutoAnnotationRequest _$AutoAnnotationRequestFromJson(
  Map<String, dynamic> json,
) => AutoAnnotationRequest(
  content: json['content'] as String,
  prompt: json['prompt'] as String?,
  modelId: (json['modelId'] as num).toInt(),
  annotationId: (json['annotationId'] as num).toInt(),
  datasetId: (json['datasetId'] as num).toInt(),
  image: json['image'] as bool,
);

Map<String, dynamic> _$AutoAnnotationRequestToJson(
  AutoAnnotationRequest instance,
) => <String, dynamic>{
  'content': instance.content,
  'prompt': instance.prompt,
  'modelId': instance.modelId,
  'annotationId': instance.annotationId,
  'datasetId': instance.datasetId,
  'image': instance.image,
};
