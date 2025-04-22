import 'package:auto_ml/common/base_response.dart';
import 'package:auto_ml/utils/toast_utils.dart';
import 'package:dio/dio.dart';

class DioClient {
  DioClient._internal();

  static final DioClient _instance = DioClient._internal();

  factory DioClient() => _instance;

  Dio? _dio;

  /// 初始化 Dio，必须手动调用一次
  void init({required String baseUrl, Map<String, dynamic>? headers}) {
    _dio = Dio(
      BaseOptions(
        baseUrl: baseUrl,
        connectTimeout: const Duration(seconds: 10),
        receiveTimeout: const Duration(seconds: 180), // 读取超时重点设置
        sendTimeout: const Duration(seconds: 10),
        headers: headers ?? {'Content-Type': 'application/json'},
      ),
    );
    _dio!.interceptors.add(
      InterceptorsWrapper(
        onResponse: (response, handler) {
          try {
            final data = response.data;
            // 你这里要确认 response.data 是 Map<String, dynamic>
            final baseResponse = BaseResponse.fromJson(
              data,
              (json) => json, // 这里只是做基础校验，不做 data 解析
            );

            if (baseResponse.code != 200) {
              throw Exception("请求失败");
            }

            // 正常响应
            handler.next(response);
          } catch (e) {
            // 抛出任何解析异常
            handler.reject(
              DioException(requestOptions: response.requestOptions, error: e),
            );

            ToastUtils.error(null, title: "请求失败");
          }
        },
      ),
    );
  }

  /// 获取 Dio 实例，必须先 init，否则报错
  Dio get instance {
    if (_dio == null) {
      throw Exception('DioClient not initialized. Call init() first.');
    }
    return _dio!;
  }
}
