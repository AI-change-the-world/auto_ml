import 'package:auto_ml/api.dart';
import 'package:auto_ml/common/base_response.dart';
import 'package:auto_ml/modules/task/models/base_model_response.dart';
import 'package:auto_ml/utils/dio_instance.dart';
import 'package:auto_ml/utils/logger.dart';
import 'package:auto_ml/utils/toast_utils.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

final baseModelsProvider = FutureProvider.family<List<BaseModel>, int>((
  ref,
  typeId,
) async {
  try {
    final response = await DioClient().instance.get(
      Api.baseModelsTypeList.replaceAll("{type}", typeId.toString()),
    );
    if (response.statusCode == 200) {
      BaseResponse<BaseModelResponse> baseResponse = BaseResponse.fromJson(
        response.data,
        (j) => BaseModelResponse.fromJson({"models": j}),
      );
      return baseResponse.data?.models ?? [];
    } else {
      throw Exception('Failed to load task models');
    }
  } catch (e) {
    logger.e(e);
    ToastUtils.error(null, title: "Failed to load models");
    return [];
  }
});
