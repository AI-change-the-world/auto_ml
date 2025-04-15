// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'annotation_list_response.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

AnnotationListResponse _$AnnotationListResponseFromJson(
        Map<String, dynamic> json) =>
    AnnotationListResponse(
      annotations: (json['annotations'] as List<dynamic>)
          .map((e) => Annotation.fromJson(e as Map<String, dynamic>))
          .toList(),
    );

Map<String, dynamic> _$AnnotationListResponseToJson(
        AnnotationListResponse instance) =>
    <String, dynamic>{
      'annotations': instance.annotations,
    };

Annotation _$AnnotationFromJson(Map<String, dynamic> json) => Annotation(
      id: (json['id'] as num).toInt(),
      datasetId: (json['datasetId'] as num).toInt(),
      annotatedFileCount: (json['annotatedFileCount'] as num).toInt(),
      annotationType: (json['annotationType'] as num).toInt(),
      updatedAt: DateTime.parse(json['updatedAt'] as String),
      isDeleted: (json['isDeleted'] as num).toInt(),
      createdAt: DateTime.parse(json['createdAt'] as String),
    );

Map<String, dynamic> _$AnnotationToJson(Annotation instance) =>
    <String, dynamic>{
      'id': instance.id,
      'datasetId': instance.datasetId,
      'annotatedFileCount': instance.annotatedFileCount,
      'annotationType': instance.annotationType,
      'updatedAt': instance.updatedAt.toIso8601String(),
      'isDeleted': instance.isDeleted,
      'createdAt': instance.createdAt.toIso8601String(),
    };
