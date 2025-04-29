// ignore_for_file: depend_on_referenced_packages

import 'dart:async';
import 'dart:typed_data';

import 'package:auto_ml/api.dart';
import 'package:auto_ml/common/base_response.dart';
import 'package:auto_ml/common/sse/sse.dart';
import 'package:auto_ml/modules/dataset/models/file_preview_response.dart';
import 'package:auto_ml/modules/predict/models/image_preview_model.dart';
import 'package:auto_ml/modules/predict/models/process_request.dart';
import 'package:auto_ml/modules/predict/models/video_result.dart';
import 'package:auto_ml/modules/predict/notifier/image_preview_state.dart';
import 'package:auto_ml/utils/dio_instance.dart';
import 'package:auto_ml/utils/logger.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:http/http.dart' as http;
import 'package:image/image.dart' as img;

class ImagePreviewNotifier
    extends AutoDisposeFamilyNotifier<ImagePreviewState, int> {
  final dio = DioClient().instance;
  late final StreamController<String> ss = StreamController.broadcast();

  Stream<String> get stream => ss.stream;
  @override
  ImagePreviewState build(int arg) {
    ref.onDispose(() {
      ss.close();
    });

    Future.microtask(() => load(arg));

    return ImagePreviewState(loading: true);
  }

  Future<void> load(int fileId) async {
    ProcessRequest request = ProcessRequest(fileId: fileId);

    sse(Api.baseUrl + Api.processVideoData, request.toJson(), ss);
  }

  Future<Image?> cropImage(Rect cropRect) async {
    final url = state.images[state.current].url;
    if (url == "") {
      return null;
    }

    final image = await _cropNetworkImage(url, cropRect);
    return image;
  }

  Future<Image> _cropNetworkImage(String url, Rect cropRect) async {
    final response = await http.get(Uri.parse(url));
    final bytes = response.bodyBytes;

    // 解码为 image 包的图像对象
    final original = img.decodeImage(bytes)!;

    // 裁剪区域坐标（确保在图像范围内）
    final cropped = img.copyCrop(
      original,
      x: cropRect.left.toInt(),
      y: cropRect.top.toInt(),
      width: cropRect.width.toInt(),
      height: cropRect.height.toInt(),
    );

    // 编码回 Uint8List
    final croppedBytes = Uint8List.fromList(img.encodePng(cropped));

    // 返回 Flutter 可用的 Image
    return Image.memory(croppedBytes);
  }

  setDone() {
    state = state.copyWith(loading: false);
  }

  changeCurrentRect(Rect rect) {
    print("change current");
    state = state.copyWith(selected: rect);
  }

  showSidebar() {
    state = state.copyWith(isSidebarOpen: true, selected: null);
  }

  hideSidebar() {
    state = state.copyWith(isSidebarOpen: false, selected: null);
  }

  Future<String> getUrl(String key) async {
    try {
      final res = await dio.get(Api.s3preview, queryParameters: {"name": key});
      BaseResponse<FilePreviewResponse> resdata = BaseResponse.fromJson(
        res.data,
        (d) => FilePreviewResponse.fromJson(d as Map<String, dynamic>),
      );
      return resdata.data?.content ?? "";
    } catch (e) {
      logger.e(e);
      return "";
    }
  }

  void setCurrent(ImagePreviewModel model) {
    int index = state.images.indexWhere(
      (element) => element.imageKey == model.imageKey,
    );
    state = state.copyWith(current: index);
  }

  void setData(VideoResult data) async {
    // state = state.copyWith()
    List<ImagePreviewModel> models = [];
    for (final i in data.keyframes) {
      models.add(
        ImagePreviewModel(
          imageKey: i.filename,
          url: "",
          label: i.filename,
          detections: i.detections,
        ),
      );
    }
    state = state.copyWith(
      images: models,
      duration: data.duration,
      imageWidth: data.frameWidth.toDouble(),
      imageHeight: data.frameHeight.toDouble(),
      loading: false,
    );
  }

  updateImageUrl(String imageKey, String url) {
    state = state.copyWith(
      images:
          state.images.map((e) {
            if (e.imageKey == imageKey) {
              return e.copyWith(url: url);
            }
            return e;
          }).toList(),
    );
  }
}

final imagePreviewProvider = AutoDisposeNotifierProvider.family<
  ImagePreviewNotifier,
  ImagePreviewState,
  int
>(() => ImagePreviewNotifier());
