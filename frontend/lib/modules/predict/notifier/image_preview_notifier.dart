import 'dart:async';

import 'package:auto_ml/api.dart';
import 'package:auto_ml/common/sse/sse.dart';
import 'package:auto_ml/modules/predict/models/process_request.dart';
import 'package:auto_ml/modules/predict/notifier/image_preview_state.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class ImagePreviewNotifier
    extends AutoDisposeFamilyNotifier<ImagePreviewState, int> {
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

  setDone() {
    state = state.copyWith(loading: false);
  }
}

final imagePreviewProvider = AutoDisposeNotifierProvider.family<
  ImagePreviewNotifier,
  ImagePreviewState,
  int
>(() => ImagePreviewNotifier());
