import 'dart:convert';
import 'dart:typed_data';
import 'dart:ui' as ui;

import 'package:auto_ml/api.dart';
import 'package:auto_ml/common/base_response.dart';
import 'package:auto_ml/modules/deploy/models/predict_single_image_request.dart';
import 'package:auto_ml/modules/predict/models/video_result.dart';
import 'package:auto_ml/utils/dio_instance.dart';
import 'package:auto_ml/utils/logger.dart';
import 'package:auto_ml/utils/toast_utils.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

final predictSingleImageProvider = AutoDisposeFutureProvider.family<
  (SingleImageResponse?, Size)?,
  PredictSingleImageRequest
>((ref, data) async {
  try {
    final response = await DioClient().instance.post(
      Api.predictSingleImage,
      data: data.toJson(),
    );
    logger.i(response.data);
    BaseResponse<SingleImageResponse> bs =
        BaseResponse<SingleImageResponse>.fromJson(
          response.data,
          (json) => SingleImageResponse.fromJson(json as Map<String, dynamic>),
        );
    Size s = await getImageSizeFromBase64(data.data);
    return (bs.data, s);
  } catch (e, s) {
    logger.e(e.toString());
    logger.e(s);
    ToastUtils.error(null, title: "Detect error");
  }

  return null;
});

Future<Size> getImageSizeFromBase64(String base64Str) async {
  Uint8List imageBytes = base64Decode(base64Str);

  final codec = await ui.instantiateImageCodec(imageBytes);
  final frame = await codec.getNextFrame();
  final image = frame.image;

  return Size(image.width.toDouble(), image.height.toDouble());
}
