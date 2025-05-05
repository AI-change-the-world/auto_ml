// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'paginate_request.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

PaginateRequest _$PaginateRequestFromJson(Map<String, dynamic> json) =>
    PaginateRequest(
      pageId: (json['pageId'] as num?)?.toInt() ?? 1,
      pageSize: (json['pageSize'] as num?)?.toInt() ?? 10,
    );

Map<String, dynamic> _$PaginateRequestToJson(PaginateRequest instance) =>
    <String, dynamic>{
      'pageId': instance.pageId,
      'pageSize': instance.pageSize,
    };
