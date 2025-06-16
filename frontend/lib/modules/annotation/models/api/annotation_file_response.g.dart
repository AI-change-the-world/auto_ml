// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'annotation_file_response.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

AnnotationFileResponse _$AnnotationFileResponseFromJson(
  Map<String, dynamic> json,
) => AnnotationFileResponse(
  annotationId: (json['annotationId'] as num).toInt(),
  annotationPath: json['annotationPath'] as String,
  files: (json['files'] as List<dynamic>).map((e) => e as String).toList(),
  classes: (json['classes'] as List<dynamic>).map((e) => e as String).toList(),
  storageType: (json['storageType'] as num).toInt(),
);

Map<String, dynamic> _$AnnotationFileResponseToJson(
  AnnotationFileResponse instance,
) => <String, dynamic>{
  'annotationId': instance.annotationId,
  'annotationPath': instance.annotationPath,
  'files': instance.files,
  'classes': instance.classes,
  'storageType': instance.storageType,
};
