import 'package:auto_ml/api.dart';
import 'package:auto_ml/common/base_response.dart';
import 'package:auto_ml/modules/annotation/models/label_img_response.dart';
import 'package:auto_ml/modules/deploy/models/predict_single_image_request.dart';
import 'package:auto_ml/utils/dio_instance.dart';
import 'package:auto_ml/utils/logger.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

final predictSingleImageProvider =
    AutoDisposeFutureProvider.family<LabelImgData?, PredictSingleImageRequest>((
      ref,
      data,
    ) async {
      try {
        final response = await DioClient().instance.post(
          Api.predictSingleImage,
          data: data.toJson(),
        );
        BaseResponse<LabelImgData> bs = BaseResponse<LabelImgData>.fromJson(
          response.data,
          (json) => LabelImgData.fromJson(json as Map<String, dynamic>),
        );
        return bs.data;
      } catch (e, s) {
        logger.e(e.toString());
        logger.e(s);
      }

      return null;
    });
