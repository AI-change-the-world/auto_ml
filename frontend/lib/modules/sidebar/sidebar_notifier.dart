import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class SidebarNotifier extends AutoDisposeNotifier<int> {
  final PageController pageController = PageController();

  @override
  int build() {
    pageController.addListener(() {
      state = pageController.page!.round();
    });
    return 0;
  }

  void setIndex(int index) {
    state = index;
    pageController.jumpToPage(index);
  }
}

final sidebarProvider = AutoDisposeNotifierProvider<SidebarNotifier, int>(
  SidebarNotifier.new,
);
