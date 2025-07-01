import 'dart:async';
import 'dart:convert';

import 'package:auto_ml/api.dart';
import 'package:auto_ml/common/base_sse_response.dart';
import 'package:auto_ml/common/sse/sse.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class DescribeImagesState {
  final String data;
  final bool isGenerating;

  DescribeImagesState({this.data = "", this.isGenerating = false});

  DescribeImagesState copyWith({String? data, bool? isGenerating}) {
    return DescribeImagesState(
      data: data ?? this.data,
      isGenerating: isGenerating ?? this.isGenerating,
    );
  }

  @override
  String toString() {
    return 'DescribeImagesState(data: $data, isGenerating: $isGenerating)';
  }
}

class DescribeImagesNotifier extends AutoDisposeNotifier<DescribeImagesState> {
  late final StreamController<String> ss = StreamController.broadcast();
  String _totalData = "";
  late final ScrollController scrollController = ScrollController();

  Stream<String> get stream => ss.stream;

  @override
  DescribeImagesState build() {
    stream.listen(addData);
    ref.onDispose(() {
      scrollController.dispose();
      ss.close();
    });
    return DescribeImagesState();
  }

  Future<void> chat(List<String> files) async {
    clear();
    Map<String, dynamic> data = {"frames": files};
    sse(Api.baseUrl + Api.describeImageList, data, ss);
  }

  Future<void> chatSingleFile(List<String> files, String prompt) async {
    clear();
    Map<String, dynamic> data = {"frames": files, "prompt": prompt};
    sse(
      Api.baseUrl + Api.describeImage,
      data,
      ss,
      onDone: (p0) {
        if (p0.isNotEmpty) {
          final list = p0.split("\n");
          StringBuffer sb = StringBuffer();
          for (var i in list) {
            if (i.isEmpty) {
              continue;
            }
            i = i.replaceFirst("data:", "");
            final sseResponse = SseResponse.fromJson(
              jsonDecode(i),
              (d) => d.toString(),
            );

            final clean = (sseResponse.data ?? "").replaceFirst("data: ", "");
            if (clean.contains("[DONE]") || clean.contains("None")) {
              continue;
            }
            if (clean.isEmpty) {
              sb.write("\n");
            } else {
              sb.write(clean);
            }
          }

          state = state.copyWith(data: sb.toString());
        }
      },
    );
  }

  void clear() {
    _totalData = "";
    state = DescribeImagesState();
  }

  void addData(String raw) {
    state = state.copyWith(isGenerating: true);
    try {
      final sseResponse = SseResponse.fromJson(
        jsonDecode(raw),
        (d) => d.toString(),
      );

      final clean = (sseResponse.data ?? "").replaceFirst("data: ", "");
      if (clean.contains("[DONE]")) {
        state = state.copyWith(isGenerating: false);
        return;
      }

      if (!clean.contains("[DONE]") && !clean.contains("None")) {
        if (clean.isEmpty) {
          _totalData += "\n";
        } else {
          _totalData += clean;
        }
      }

      if (state.data != _totalData) {
        state = state.copyWith(data: _totalData);
        scrollController.jumpTo(scrollController.position.maxScrollExtent);
      }
    } catch (_) {
      state = state.copyWith(isGenerating: false);
    }
  }
}

final describeImagesProvider = AutoDisposeNotifierProvider(
  () => DescribeImagesNotifier(),
);
