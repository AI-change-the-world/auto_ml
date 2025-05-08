// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'dataset_evalation_request.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

DatasetEvalationRequest _$DatasetEvalationRequestFromJson(
        Map<String, dynamic> json) =>
    DatasetEvalationRequest(
      datasetId: (json['datasetId'] as num).toInt(),
      annotationId: (json['annotationId'] as num).toInt(),
    );

Map<String, dynamic> _$DatasetEvalationRequestToJson(
        DatasetEvalationRequest instance) =>
    <String, dynamic>{
      'datasetId': instance.datasetId,
      'annotationId': instance.annotationId,
    };
