import 'package:auto_ml/api.dart';
import 'package:auto_ml/common/base_response.dart';
import 'package:auto_ml/utils/dio_instance.dart';

Future<String> getPresignUrl(String path) async {
  final res = await DioClient().instance.post(
    Api.getAugData,
    data: {"path": path},
  );
  final BaseResponse<String> response = BaseResponse.fromJson(
    res.data,
    (json) => json as String,
  );
  return response.data.toString();
}
