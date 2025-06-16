import 'package:auto_ml/api.dart';
import 'package:auto_ml/common/base_response.dart';
import 'package:auto_ml/modules/home/models/home_index_response.dart';
import 'package:auto_ml/utils/dio_instance.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

final homeIndexProvider = FutureProvider.autoDispose<HomeIndexResponse?>((
  ref,
) async {
  final dio = DioClient().instance;
  final response = await dio.get(Api.homeIndex);

  final baseResponse = BaseResponse.fromJson(
    response.data,
    (json) => HomeIndexResponse.fromJson(json as Map<String, dynamic>),
  );

  return baseResponse.data;
}, name: "homeIndexProvider");
