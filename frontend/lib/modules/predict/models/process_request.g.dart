// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'process_request.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

ProcessRequest _$ProcessRequestFromJson(Map<String, dynamic> json) =>
    ProcessRequest(
      fileId: (json['fileId'] as num).toInt(),
      methodId: (json['methodId'] as num?)?.toInt() ?? -1,
    );

Map<String, dynamic> _$ProcessRequestToJson(ProcessRequest instance) =>
    <String, dynamic>{'fileId': instance.fileId, 'methodId': instance.methodId};
