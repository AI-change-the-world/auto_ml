import 'package:dio/dio.dart';

void main() async {
  final dio = Dio();

  dio
      .post(
        "http://localhost:8080/automl/dataset/file/preview",
        data: {
          "baseUrl":
              "/Users/guchengxi/Desktop/projects/auto_ml/frontend/dataset/images/",
          "storageType": 0,
          "path": "test.png",
        },
      )
      .then((r) {
        // ignore: avoid_print
        print(r.data);
      });
}
