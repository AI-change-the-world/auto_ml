import 'package:auto_ml/modules/dataset/dataset_screen.dart';
import 'package:auto_ml/modules/label/label_screen.dart';
import 'package:auto_ml/modules/models/model_screen.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:he/he.dart';

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
      // body: Row(
      //   children: [
      //     const Sidebar(),
      //     Expanded(
      //       child: PageView(
      //         physics: const NeverScrollableScrollPhysics(),
      //         controller: ref.read(sidebarProvider.notifier).pageController,
      //         children: [DatasetScreen(), LabelScreen(), Container()],
      //       ),
      //     ),
      //   ],
      // ),
      body: SimpleLayout(
        elevation: 10,
        decoration: BoxDecoration(borderRadius: BorderRadius.circular(10)),
        items: [
          SidebarItem(
            icon: const Icon(Icons.dataset, color: Colors.blueAccent),
            iconInactive: const Icon(Icons.dataset),
            index: 0,
            title: "Datasets",
          ),
          SidebarItem(
            icon: const Icon(Icons.rule, color: Colors.blueAccent),
            iconInactive: const Icon(Icons.rule),
            index: 2,
            title: "Label",
          ),
          SidebarItem(
            icon: const Icon(Icons.text_fields, color: Colors.blueAccent),
            iconInactive: const Icon(Icons.text_fields),
            index: 3,
            title: "Test",
          ),
          SidebarItem(
            icon: const Icon(Icons.list, color: Colors.blueAccent),
            iconInactive: const Icon(Icons.list),
            index: 1,
            title: "Models",
          ),
        ]..sort((a, b) => a.index.compareTo(b.index)),
        children: [DatasetScreen(), ModelScreen(), LabelScreen(), Container()],
      ),
    );
  }
}
