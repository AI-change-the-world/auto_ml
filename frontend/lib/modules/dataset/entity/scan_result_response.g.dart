// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'scan_result_response.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

ScanResultResponse _$ScanResultResponseFromJson(Map<String, dynamic> json) =>
    ScanResultResponse(
      filePaths:
          (json['filePaths'] as List<dynamic>).map((e) => e as String).toList(),
      status: (json['status'] as num).toInt(),
      count: (json['count'] as num).toInt(),
    );

Map<String, dynamic> _$ScanResultResponseToJson(ScanResultResponse instance) =>
    <String, dynamic>{
      'filePaths': instance.filePaths,
      'status': instance.status,
      'count': instance.count,
    };
