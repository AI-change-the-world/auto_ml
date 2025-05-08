// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'new_annotation_request.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

NewAnnotationRequest _$NewAnnotationRequestFromJson(
        Map<String, dynamic> json) =>
    NewAnnotationRequest(
      datasetId: (json['datasetId'] as num).toInt(),
      storageType: (json['storageType'] as num).toInt(),
      savePath: json['savePath'] as String?,
      username: json['username'] as String?,
      password: json['password'] as String?,
      type: (json['type'] as num).toInt(),
      classes: json['classes'] as String,
    );

Map<String, dynamic> _$NewAnnotationRequestToJson(
        NewAnnotationRequest instance) =>
    <String, dynamic>{
      'datasetId': instance.datasetId,
      'storageType': instance.storageType,
      'savePath': instance.savePath,
      'username': instance.username,
      'password': instance.password,
      'type': instance.type,
      'classes': instance.classes,
    };
