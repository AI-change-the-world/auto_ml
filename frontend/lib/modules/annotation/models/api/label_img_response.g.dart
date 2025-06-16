// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'label_img_response.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

LabelImgData _$LabelImgDataFromJson(Map<String, dynamic> json) => LabelImgData(
  imagePath: json['image_path'] as String?,
  labels:
      (json['labels'] as List<dynamic>?)
          ?.map((e) => Labels.fromJson(e as Map<String, dynamic>))
          .toList(),
);

Map<String, dynamic> _$LabelImgDataToJson(LabelImgData instance) =>
    <String, dynamic>{
      'image_path': instance.imagePath,
      'labels': instance.labels,
    };

Labels _$LabelsFromJson(Map<String, dynamic> json) => Labels(
  label: json['label'] as String?,
  xCenter: (json['x_center'] as num?)?.toDouble(),
  yCenter: (json['y_center'] as num?)?.toDouble(),
  width: (json['width'] as num?)?.toDouble(),
  height: (json['height'] as num?)?.toDouble(),
);

Map<String, dynamic> _$LabelsToJson(Labels instance) => <String, dynamic>{
  'label': instance.label,
  'x_center': instance.xCenter,
  'y_center': instance.yCenter,
  'width': instance.width,
  'height': instance.height,
};
