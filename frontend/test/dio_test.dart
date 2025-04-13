import 'package:auto_ml/common/base_response.dart';
import 'package:auto_ml/modules/api/request/label_img_request.dart';
import 'package:auto_ml/modules/api/response/label_img_response.dart';
import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';

void main() async {
  Dio dio = Dio();
  LabelImgRequest request = LabelImgRequest(
    imagePath:
        '/Users/guchengxi/Desktop/projects/auto_ml/backend/datasets/coco8/images/train/000000000030.jpg',
    classes: ["vase", "flower"],
  );
  dio.post("http://127.0.0.1:8000/label/image", data: request.toJson()).then((
    d,
  ) {
    BaseResponse<LabelImgData> response = BaseResponse.fromJson(d.data, (data) {
      return LabelImgData.fromJson(data as Map<String, dynamic>);
    });
    if (kDebugMode) {
      print(response.data?.labels);
    }
  });
}
