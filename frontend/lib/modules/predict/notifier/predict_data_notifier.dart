import 'dart:async';

import 'package:auto_ml/api.dart';
import 'package:auto_ml/common/base_response.dart';
import 'package:auto_ml/modules/predict/models/predict_list_response.dart';
import 'package:auto_ml/modules/predict/notifier/predict_data_state.dart';
import 'package:auto_ml/utils/dio_instance.dart';
import 'package:auto_ml/utils/logger.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class PredictDataNotifier extends AutoDisposeAsyncNotifier<PredictDataState> {
  final dio = DioClient().instance;

  @override
  FutureOr<PredictDataState> build() async {
    try {
      final response = await dio.get(Api.predictList);
      BaseResponse baseResponse = BaseResponse.fromJson(
        response.data,
        (json) => PredictListResponse.fromJson({"data": json}),
      );
      return PredictDataState(data: baseResponse.data?.data ?? []);
    } catch (e) {
      logger.e("Get list error $e");
      return PredictDataState();
    }
  }
}

final predictDataProvider =
    AutoDisposeAsyncNotifierProvider<PredictDataNotifier, PredictDataState>(
      () => PredictDataNotifier(),
    );
