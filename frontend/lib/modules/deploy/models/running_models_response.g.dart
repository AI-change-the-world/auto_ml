// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'running_models_response.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

RunningModelsResponse _$RunningModelsResponseFromJson(
  Map<String, dynamic> json,
) => RunningModelsResponse(
  runningModels:
      (json['running_models'] as List<dynamic>)
          .map((e) => (e as num).toInt())
          .toList(),
);

Map<String, dynamic> _$RunningModelsResponseToJson(
  RunningModelsResponse instance,
) => <String, dynamic>{'running_models': instance.runningModels};
