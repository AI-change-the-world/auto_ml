import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class DatasetPageNotifier extends AutoDisposeNotifier<int> {
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

final datasetPageProvider =
    AutoDisposeNotifierProvider<DatasetPageNotifier, int>(
      DatasetPageNotifier.new,
    );
