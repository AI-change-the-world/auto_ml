// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'modify_dataset_request.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

ModifyDatasetRequest _$ModifyDatasetRequestFromJson(
        Map<String, dynamic> json) =>
    ModifyDatasetRequest(
      name: json['name'] as String,
      description: json['description'] as String,
      storageType: (json['storageType'] as num).toInt(),
      ranking: (json['ranking'] as num).toDouble(),
      url: json['url'] as String,
      username: json['username'] as String?,
      password: json['password'] as String?,
      id: (json['id'] as num).toInt(),
    );

Map<String, dynamic> _$ModifyDatasetRequestToJson(
        ModifyDatasetRequest instance) =>
    <String, dynamic>{
      'name': instance.name,
      'description': instance.description,
      'storageType': instance.storageType,
      'ranking': instance.ranking,
      'url': instance.url,
      'username': instance.username,
      'password': instance.password,
      'id': instance.id,
    };
