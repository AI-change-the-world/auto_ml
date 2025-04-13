import 'dart:async';
import 'dart:convert';

import 'package:auto_ml/utils/dio_instance.dart';
import 'package:auto_ml/utils/logger.dart';
import 'package:dio/dio.dart';

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
  final instance = DioClient().instance;

  try {
    final response = await instance.post(
      url,
      data: data,
      options: Options(headers: header, responseType: ResponseType.stream),
    );

    final stream = response.data!.stream;

    // 解码 + 拆行
    stream.transform(utf8.decoder).transform(const LineSplitter()).listen((
      line,
    ) {
      if (line.startsWith('data:')) {
        final message = line.substring(5).trim();
        ss.sink.add(message);
      }
    });
  } catch (e) {
    logger.e("error $e");
  }
}
