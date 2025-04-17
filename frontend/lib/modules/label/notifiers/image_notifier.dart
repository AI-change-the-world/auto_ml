import 'dart:async';
import 'dart:ui' as ui;

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:riverpod/riverpod.dart';

class ImageState {
  ui.Image? image;
  Size size;
  String current;

  ImageState({this.image, this.size = const Size(0, 0), this.current = ""});

  ImageState copyWith({ui.Image? image, Size? size, String? current}) {
    return ImageState(
      image: image ?? this.image,
      size: size ?? this.size,
      current: current ?? this.current,
    );
  }
}

class ImageNotifier extends AutoDisposeFamilyAsyncNotifier<ImageState, String> {
  @override
  FutureOr<ImageState> build(String arg) async {
    if (arg.isEmpty) {
      return ImageState(current: arg);
    }

    final r = await _loadImage(arg);
    return ImageState(image: r.$1, size: r.$2, current: arg);
  }

  Future<(ui.Image, Size)> _loadImage(String current) async {
    if (current.isEmpty) {
      throw Exception("No image path provided");
    }

    if (current.startsWith("asset")) {
      final List<int> bytes =
          (await rootBundle.load(current)).buffer.asUint8List();
      final ui.Image image = await decodeImageFromList(
        Uint8List.fromList(bytes),
      );

      return (image, Size(image.width.toDouble(), image.height.toDouble()));
    } else if (current.startsWith("data:")) {
      /// TODO: load image from base64
      throw Exception("unimplemented");
    } else {
      /// TODO: load image from url
      throw Exception("unimplemented");
    }
  }
}

final imageNotifierProvider =
    AutoDisposeAsyncNotifierProvider.family<ImageNotifier, ImageState, String>(
      ImageNotifier.new,
    );
