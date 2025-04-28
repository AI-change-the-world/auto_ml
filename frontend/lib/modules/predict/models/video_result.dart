import 'package:json_annotation/json_annotation.dart';

part 'video_result.g.dart'; // 生成的文件

@JsonSerializable()
class VideoResult {
  final String videoPath;
  final double duration;
  final int frameWidth;
  final int frameHeight;
  final List<Keyframe> keyframes;

  VideoResult({
    required this.videoPath,
    required this.duration,
    required this.frameWidth,
    required this.frameHeight,
    required this.keyframes,
  });

  factory VideoResult.fromJson(Map<String, dynamic> json) =>
      _$VideoResultFromJson(json);
  Map<String, dynamic> toJson() => _$VideoResultToJson(this);
}

@JsonSerializable()
class Keyframe {
  final String filename;
  final double timestamp;
  final List<Detection> detections;

  Keyframe({
    required this.filename,
    required this.timestamp,
    required this.detections,
  });

  factory Keyframe.fromJson(Map<String, dynamic> json) =>
      _$KeyframeFromJson(json);
  Map<String, dynamic> toJson() => _$KeyframeToJson(this);
}

@JsonSerializable()
class Detection {
  final String name;
  @JsonKey(name: 'obj_class')
  final int objClass;
  final double confidence;
  final Box box;

  Detection({
    required this.name,
    required this.objClass,
    required this.confidence,
    required this.box,
  });

  factory Detection.fromJson(Map<String, dynamic> json) =>
      _$DetectionFromJson(json);
  Map<String, dynamic> toJson() => _$DetectionToJson(this);
}

@JsonSerializable()
class Box {
  final double x1;
  final double y1;
  final double x2;
  final double y2;

  Box({required this.x1, required this.y1, required this.x2, required this.y2});

  factory Box.fromJson(Map<String, dynamic> json) => _$BoxFromJson(json);
  Map<String, dynamic> toJson() => _$BoxToJson(this);
}
