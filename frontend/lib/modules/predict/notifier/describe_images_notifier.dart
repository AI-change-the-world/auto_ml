import 'dart:async';
import 'dart:convert';

import 'package:auto_ml/api.dart';
import 'package:auto_ml/common/base_sse_response.dart';
import 'package:auto_ml/common/sse/sse.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class DescribeImagesNotifier extends AutoDisposeNotifier<String> {
  late final StreamController<String> ss = StreamController.broadcast();
  String _totalData = "";
  late final ScrollController scrollController = ScrollController();

  Stream<String> get stream => ss.stream;

  @override
  String build() {
    stream.listen(addData);
    ref.onDispose(() {
      scrollController.dispose();
      ss.close();
    });
    return "";
  }

  chat(List<String> files) async {
    clear();
    Map<String, dynamic> data = {"frames": files};
    sse(Api.baseUrl + Api.describeImageList, data, ss);
  }

  clear() {
    _totalData = "";
    state = "";
  }

  void addData(String raw) {
    try {
      final sseResponse = SseResponse.fromJson(
        jsonDecode(raw),
        (d) => d.toString(),
      );

      final clean = (sseResponse.data ?? "").replaceFirst("data: ", "");
      if (!clean.contains("[DONE]") && !clean.contains("None")) {
        if (clean.isEmpty) {
          _totalData += "\n";
        } else {
          _totalData += clean;
        }
      }

      if (state != _totalData) {
        state = _totalData;
        scrollController.jumpTo(scrollController.position.maxScrollExtent);
      }
    } catch (_) {}
  }
}

final describeImagesProvider = AutoDisposeNotifierProvider(
  () => DescribeImagesNotifier(),
);
