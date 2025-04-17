import 'dart:async';
import 'dart:convert';
import 'dart:ui' as ui;

import 'package:auto_ml/modules/current_dataset_annotation_notifier.dart';
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

class ImageNotifier extends AutoDisposeAsyncNotifier<ImageState> {
  @override
  FutureOr<ImageState> build() async {
    String current =
        ref.read(currentDatasetAnnotationNotifierProvider).currentData;

    final r = await _loadImage(current);
    return ImageState(image: r.$1, size: r.$2, current: current);
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
      final String base64Str = current.split(',').last;
      final List<int> bytes = base64Decode(base64Str);
      final ui.Image image = await decodeImageFromList(
        Uint8List.fromList(bytes),
      );
      return (image, Size(image.width.toDouble(), image.height.toDouble()));
    } else {
      /// TODO: load image from url
      throw Exception("unimplemented");
    }
  }
}

final imageNotifierProvider =
    AutoDisposeAsyncNotifierProvider<ImageNotifier, ImageState>(
      ImageNotifier.new,
    );
