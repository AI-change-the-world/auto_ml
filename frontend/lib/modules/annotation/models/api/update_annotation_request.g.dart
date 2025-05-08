// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'update_annotation_request.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

UpdateAnnotationRequest _$UpdateAnnotationRequestFromJson(
        Map<String, dynamic> json) =>
    UpdateAnnotationRequest(
      content: json['content'] as String,
      annotationPath: json['annotationPath'] as String,
    );

Map<String, dynamic> _$UpdateAnnotationRequestToJson(
        UpdateAnnotationRequest instance) =>
    <String, dynamic>{
      'content': instance.content,
      'annotationPath': instance.annotationPath,
    };
