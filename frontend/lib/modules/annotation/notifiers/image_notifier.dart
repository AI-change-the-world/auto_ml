import 'dart:async';
import 'dart:convert';
import 'dart:ui' as ui;

import 'package:auto_ml/utils/logger.dart';
import 'package:auto_ml/utils/toast_utils.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:riverpod/riverpod.dart';
// ignore: depend_on_referenced_packages
import 'package:http/http.dart' as http;

class ImageState {
  ui.Image? image;
  Size size;
  String imgKey;

  ImageState({this.size = const Size(0, 0), this.image, this.imgKey = ""});

  ImageState copyWith({Size? size, ui.Image? image, String? imgKey}) {
    return ImageState(
      size: size ?? this.size,
      imgKey: imgKey ?? this.imgKey,
      image: image ?? this.image,
    );
  }

  @override
  String toString() {
    return "ImageState(size: $size, imgKey: $imgKey)";
  }
}

class ImageNotifier extends Notifier<ImageState> {
  @override
  ImageState build() {
    return ImageState();
  }

  Future<void> loadImage(String current, String imgPath) async {
    if (imgPath == state.imgKey) {
      logger.d("Image already loaded");
      return;
    }

    if (current.isEmpty) {
      ToastUtils.error(null, title: "No image path/data provided");
      return;
    }
    var data = await _loadImage(current);
    state = state.copyWith(size: data.$2, image: data.$1, imgKey: imgPath);
    logger.d("loaded image $imgPath");
  }

  Future<(ui.Image, Size)> _loadImage(String current) async {
    if (current.startsWith("asset")) {
      final List<int> bytes =
          (await rootBundle.load(current)).buffer.asUint8List();
      final ui.Image image = await decodeImageFromList(
        Uint8List.fromList(bytes),
      );

      return (image, Size(image.width.toDouble(), image.height.toDouble()));
    } else if (current.startsWith("data:")) {
      final String base64Str = current.split(',').last;
      final List<int> bytes = base64Decode(base64Str);
      final ui.Image image = await decodeImageFromList(
        Uint8List.fromList(bytes),
      );
      return (image, Size(image.width.toDouble(), image.height.toDouble()));
    } else if (current.startsWith("http")) {
      logger.d("Loading image from $current");
      final http.Response response = await http.get(Uri.parse(current));
      if (response.statusCode != 200) {
        throw Exception("Failed to load image from network");
      }
      final Uint8List bytes = response.bodyBytes;
      final ui.Image image = await decodeImageFromList(bytes);
      return (image, Size(image.width.toDouble(), image.height.toDouble()));
    } else {
      /// TODO: load image from url
      throw Exception("unimplemented");
    }
  }
}

final imageNotifierProvider = NotifierProvider<ImageNotifier, ImageState>(
  ImageNotifier.new,
);
