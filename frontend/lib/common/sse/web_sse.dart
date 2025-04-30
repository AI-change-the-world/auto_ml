import 'dart:async';
import 'dart:convert';
// ignore: deprecated_member_use, avoid_web_libraries_in_flutter
import 'dart:html';

import 'package:auto_ml/utils/logger.dart';

Future sse(
  String url,
  Map<String, dynamic> data,
  StreamController<String> ss, {
  Map<String, dynamic> header = const {
    "Content-Type": "application/json",
    'Accept': 'text/event-stream',
    'Cache-Control': 'no-cache',
  },
}) async {
  logger.d("sse url: $url");
  HttpRequest request = HttpRequest();
  String alreadyReceived = '';
  request
    ..timeout = 300 * 1000
    ..open('POST', url)
    ..setRequestHeader('Content-Type', 'application/json')
    ..onProgress.listen((event) {
      if (request.responseText != null) {
        var res = request.responseText!.replaceAll(alreadyReceived, '');
        alreadyReceived = request.responseText!;
        List<String> parts = res.split('\n');
        for (var part in parts) {
          if (part.startsWith('data:')) {
            // 提取 JSON 字符串
            String subString = part.substring(5).trimLeft(); // 去掉 "data:"
            if (subString.isNotEmpty) {
              ss.sink.add(subString);
            }
          }
        }
      }
    })
    ..onError.listen((err) {
      logger.e("onError $err");
      ss.sink.add("[DONE] onError $err");
    })
    ..onLoadEnd.listen((fur) {
      /// TODO 处理所有收到的数据
      /// 因为上面的数据有的时候
      /// 会有处理异常
      logger.i(request.responseText);
      ss.sink.add("[DONE]");
    })
    ..send(jsonEncode(data)); // 发送请求体
}
