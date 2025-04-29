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
