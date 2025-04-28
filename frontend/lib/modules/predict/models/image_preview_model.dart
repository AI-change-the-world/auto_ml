import 'package:auto_ml/modules/predict/models/video_result.dart';

class ImagePreviewModel {
  final String imageKey;

  /// s3 presigned url
  final String url;

  final String label;

  final Box box;

  ImagePreviewModel({
    required this.imageKey,
    required this.url,
    required this.label,
    required this.box,
  });
}
