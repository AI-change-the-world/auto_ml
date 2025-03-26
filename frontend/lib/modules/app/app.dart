import 'package:auto_ml/modules/dataset/dataset_screen.dart';
import 'package:auto_ml/modules/label/label_screen.dart';
import 'package:auto_ml/modules/sidebar/sidebar.dart';
import 'package:auto_ml/modules/sidebar/sidebar_notifier.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class App extends ConsumerStatefulWidget {
  const App({super.key});

  @override
  ConsumerState<App> createState() => _AppState();
}

class _AppState extends ConsumerState<App> {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      body: Row(
        children: [
          const Sidebar(),
          Expanded(
            child: PageView(
              physics: const NeverScrollableScrollPhysics(),
              controller: ref.read(sidebarProvider.notifier).pageController,
              children: [DatasetScreen(), LabelScreen(), Container()],
            ),
          ),
        ],
      ),
    );
  }
}
