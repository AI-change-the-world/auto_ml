import 'package:json_annotation/json_annotation.dart';

part 'video_result.g.dart'; // 生成的文件

@JsonSerializable()
class VideoResult {
  final double duration;
  @JsonKey(name: 'frame_width')
  final int frameWidth;
  @JsonKey(name: 'frame_height')
  final int frameHeight;
  final List<Keyframe> keyframes;

  VideoResult({
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

extension VideoResultDescription on VideoResult {
  String toResultString() {
    final buffer = StringBuffer();
    buffer.writeln('视频总时长：${duration.toStringAsFixed(2)} 秒');
    buffer.writeln('视频尺寸：${frameWidth}x$frameHeight');
    buffer.writeln('共提取 ${keyframes.length} 帧作为关键帧。\n');

    for (int i = 0; i < keyframes.length; i++) {
      final frame = keyframes[i];
      final detections = frame.detections;
      final personCount = detections.where((d) => d.name == 'person').length;
      final hardhatCount = detections.where((d) => d.name == 'hardhat').length;
      final noHardhatCount =
          detections.where((d) => d.name == 'no-hardhat').length;
      final safetyVestCount =
          detections
              .where(
                (d) => d.name == 'no-safety vest' || d.name == 'safety vest',
              )
              .length;
      final noVestCount =
          detections.where((d) => d.name == 'no-safety vest').length;
      final noMaskCount = detections.where((d) => d.name == 'no-mask').length;

      buffer.writeln(
        '第 ${i + 1} 帧（时间戳 ${frame.timestamp.toStringAsFixed(1)} 秒）:',
      );
      buffer.writeln('  - 检测到 ${detections.length} 个目标');
      buffer.writeln('  - 人数：$personCount');
      buffer.writeln('  - 戴安全帽：$hardhatCount，未戴安全帽：$noHardhatCount');
      buffer.writeln('  - 穿安全背心：$safetyVestCount，未穿安全背心：$noVestCount');
      buffer.writeln('  - 未戴口罩：$noMaskCount\n');
    }

    return buffer.toString();
  }
}
