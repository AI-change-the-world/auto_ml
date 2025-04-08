import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class ModelPageNotifier extends AutoDisposeNotifier<int> {
  final PageController controller = PageController(initialPage: 0);

  @override
  int build() {
    ref.onDispose(() {
      controller.dispose();
    });
    return 0;
  }

  changePage(int index) {
    if (state == index) {
      return;
    }
    state = index;
    controller.jumpToPage(index);
  }
}

final modelPageNotifierProvider =
    AutoDisposeNotifierProvider<ModelPageNotifier, int>(ModelPageNotifier.new);
