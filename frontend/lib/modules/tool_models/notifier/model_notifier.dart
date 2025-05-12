import 'dart:async';

import 'package:auto_ml/api.dart';
import 'package:auto_ml/common/base_response.dart';
import 'package:auto_ml/modules/tool_models/models/tool_model_response.dart';
import 'package:auto_ml/modules/tool_models/notifier/model_state.dart';
import 'package:auto_ml/utils/dio_instance.dart';
import 'package:auto_ml/utils/logger.dart';
import 'package:auto_ml/utils/toast_utils.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class ModelNotifier extends AutoDisposeAsyncNotifier<ModelState> {
  final dio = DioClient().instance;
  @override
  FutureOr<ModelState> build() async {
    try {
      final response = await dio.get(Api.getToolModels);
      final BaseResponse<ToolModelResponse> baseResponse =
          BaseResponse.fromJson(
            response.data,
            (j) => ToolModelResponse.fromJson({"toolModels": j}),
          );

      return ModelState(models: baseResponse.data?.toolModels ?? []);
    } catch (e, s) {
      logger.e(s);
      ToastUtils.error(null, title: "Error in getToolModels");
      return ModelState(models: []);
    }
  }
}

final modelNotifierProvider =
    AutoDisposeAsyncNotifierProvider<ModelNotifier, ModelState>(
      ModelNotifier.new,
    );
