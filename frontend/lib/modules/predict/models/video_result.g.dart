// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'video_result.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

VideoResult _$VideoResultFromJson(Map<String, dynamic> json) => VideoResult(
  duration: (json['duration'] as num).toDouble(),
  frameWidth: (json['frame_width'] as num).toInt(),
  frameHeight: (json['frame_height'] as num).toInt(),
  keyframes:
      (json['keyframes'] as List<dynamic>)
          .map((e) => Keyframe.fromJson(e as Map<String, dynamic>))
          .toList(),
);

Map<String, dynamic> _$VideoResultToJson(VideoResult instance) =>
    <String, dynamic>{
      'duration': instance.duration,
      'frame_width': instance.frameWidth,
      'frame_height': instance.frameHeight,
      'keyframes': instance.keyframes,
    };

Keyframe _$KeyframeFromJson(Map<String, dynamic> json) => Keyframe(
  filename: json['filename'] as String,
  timestamp: (json['timestamp'] as num).toDouble(),
  detections:
      (json['detections'] as List<dynamic>)
          .map((e) => Detection.fromJson(e as Map<String, dynamic>))
          .toList(),
);

Map<String, dynamic> _$KeyframeToJson(Keyframe instance) => <String, dynamic>{
  'filename': instance.filename,
  'timestamp': instance.timestamp,
  'detections': instance.detections,
};

SingleImageResponse _$SingleImageResponseFromJson(Map<String, dynamic> json) =>
    SingleImageResponse(
      imageId: json['image_id'] as String,
      results:
          (json['results'] as List<dynamic>)
              .map((e) => Detection.fromJson(e as Map<String, dynamic>))
              .toList(),
      imageWidth: (json['image_width'] as num?)?.toInt() ?? 0,
      imageHeight: (json['image_height'] as num?)?.toInt() ?? 0,
    );

Map<String, dynamic> _$SingleImageResponseToJson(
  SingleImageResponse instance,
) => <String, dynamic>{
  'image_id': instance.imageId,
  'results': instance.results,
  'image_width': instance.imageWidth,
  'image_height': instance.imageHeight,
};

Detection _$DetectionFromJson(Map<String, dynamic> json) => Detection(
  name: json['name'] as String,
  objClass: (json['obj_class'] as num).toInt(),
  confidence: (json['confidence'] as num).toDouble(),
  box: Box.fromJson(json['box'] as Map<String, dynamic>),
);

Map<String, dynamic> _$DetectionToJson(Detection instance) => <String, dynamic>{
  'name': instance.name,
  'obj_class': instance.objClass,
  'confidence': instance.confidence,
  'box': instance.box,
};

Box _$BoxFromJson(Map<String, dynamic> json) => Box(
  x1: (json['x1'] as num).toDouble(),
  y1: (json['y1'] as num).toDouble(),
  x2: (json['x2'] as num).toDouble(),
  y2: (json['y2'] as num).toDouble(),
);

Map<String, dynamic> _$BoxToJson(Box instance) => <String, dynamic>{
  'x1': instance.x1,
  'y1': instance.y1,
  'x2': instance.x2,
  'y2': instance.y2,
};
