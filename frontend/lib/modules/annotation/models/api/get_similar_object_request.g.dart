// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'get_similar_object_request.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

GetSimilarObjectRequest _$GetSimilarObjectRequestFromJson(
  Map<String, dynamic> json,
) => GetSimilarObjectRequest(
  path: json['path'] as String,
  left: (json['left'] as num).toDouble(),
  top: (json['top'] as num).toDouble(),
  right: (json['right'] as num).toDouble(),
  bottom: (json['bottom'] as num).toDouble(),
  label: json['label'] as String,
  model: (json['model'] as num?)?.toInt() ?? 1,
  id: (json['id'] as num).toInt(),
);

Map<String, dynamic> _$GetSimilarObjectRequestToJson(
  GetSimilarObjectRequest instance,
) => <String, dynamic>{
  'path': instance.path,
  'left': instance.left,
  'top': instance.top,
  'right': instance.right,
  'bottom': instance.bottom,
  'label': instance.label,
  'model': instance.model,
  'id': instance.id,
};
