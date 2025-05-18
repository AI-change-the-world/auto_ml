// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'update_annotation_prompt_request.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

UpdateAnnotationPromptRequest _$UpdateAnnotationPromptRequestFromJson(
        Map<String, dynamic> json) =>
    UpdateAnnotationPromptRequest(
      json['prompt'] as String,
      (json['annotationId'] as num).toInt(),
    );

Map<String, dynamic> _$UpdateAnnotationPromptRequestToJson(
        UpdateAnnotationPromptRequest instance) =>
    <String, dynamic>{
      'prompt': instance.prompt,
      'annotationId': instance.annotationId,
    };
