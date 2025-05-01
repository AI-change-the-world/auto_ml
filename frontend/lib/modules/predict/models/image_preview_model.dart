import 'package:auto_ml/modules/predict/models/video_result.dart';

class ImagePreviewModel {
  final String imageKey;

  /// s3 presigned url
  final String url;

  final String label;

  final List<Detection> detections;

  ImagePreviewModel({
    required this.imageKey,
    required this.url,
    required this.label,
    required this.detections,
  });

  ImagePreviewModel copyWith({
    String? imageKey,
    String? url,
    String? label,
    List<Detection>? detections,
  }) {
    return ImagePreviewModel(
      imageKey: imageKey ?? this.imageKey,
      url: url ?? this.url,
      label: label ?? this.label,
      detections: detections ?? this.detections,
    );
  }
}

extension ImagePreviewDescription on ImagePreviewModel {
  String toResultString() {
    final buffer = StringBuffer();

    final personCount = detections.where((d) => d.name == 'person').length;
    final hardhatCount = detections.where((d) => d.name == 'hardhat').length;
    final noHardhatCount =
        detections.where((d) => d.name == 'no-hardhat').length;
    final safetyVestCount =
        detections
            .where((d) => d.name == 'no-safety vest' || d.name == 'safety vest')
            .length;
    final noVestCount =
        detections.where((d) => d.name == 'no-safety vest').length;
    final noMaskCount = detections.where((d) => d.name == 'no-mask').length;

    buffer.writeln('检测到 ${detections.length} 个目标：');
    buffer.writeln('  - 人数：$personCount');
    buffer.writeln('  - 戴安全帽：$hardhatCount，未戴安全帽：$noHardhatCount');
    buffer.writeln('  - 戴安全背心：$safetyVestCount，未戴安全背心：$noVestCount');
    buffer.writeln('  - 未戴口罩：$noMaskCount');

    return buffer.toString();
  }
}
