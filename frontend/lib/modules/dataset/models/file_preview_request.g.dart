// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'file_preview_request.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

FilePreviewRequest _$FilePreviewRequestFromJson(Map<String, dynamic> json) =>
    FilePreviewRequest(
      baseUrl: json['baseUrl'] as String,
      storageType: (json['storageType'] as num).toInt(),
      path: json['path'] as String,
    );

Map<String, dynamic> _$FilePreviewRequestToJson(FilePreviewRequest instance) =>
    <String, dynamic>{
      'baseUrl': instance.baseUrl,
      'storageType': instance.storageType,
      'path': instance.path,
    };
