// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'new_dataset_request.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

NewDatasetRequest _$NewDatasetRequestFromJson(Map<String, dynamic> json) =>
    NewDatasetRequest(
      name: json['name'] as String,
      description: json['description'] as String,
      storageType: (json['storageType'] as num).toInt(),
      ranking: (json['ranking'] as num).toDouble(),
      url: json['url'] as String,
      username: json['username'] as String?,
      password: json['password'] as String?,
    );

Map<String, dynamic> _$NewDatasetRequestToJson(NewDatasetRequest instance) =>
    <String, dynamic>{
      'name': instance.name,
      'description': instance.description,
      'storageType': instance.storageType,
      'ranking': instance.ranking,
      'url': instance.url,
      'username': instance.username,
      'password': instance.password,
    };
