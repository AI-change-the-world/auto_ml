import 'dart:async';

import 'package:flutter/material.dart';

Future<Size> getImageSizeAsync(ImageProvider imageProvider) async {
  final Completer<Size> completer = Completer();

  imageProvider
      .resolve(ImageConfiguration())
      .addListener(
        ImageStreamListener((ImageInfo info, bool _) {
          Size size = Size(
            info.image.width.toDouble(),
            info.image.height.toDouble(),
          );
          completer.complete(size);
        }),
      );

  return completer.future;
}
