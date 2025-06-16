import 'package:auto_ml/modules/home/notifier/home_notifier.dart';
import 'package:auto_ml/modules/vertical_tile.dart';
import 'package:auto_ml/utils/logger.dart';
import 'package:flutter/material.dart';
import 'package:flutter_layout_grid/flutter_layout_grid.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

class HomeScreen extends ConsumerWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(homeIndexProvider);

    return state.when(
      loading: () => const Center(child: CircularProgressIndicator()),
      error: (error, stackTrace) {
        logger.e(stackTrace);
        return Center(child: Text(error.toString()));
      },

      data: (data) {
        return Padding(
          padding: const EdgeInsets.all(10.0),
          child: LayoutGrid(
            columnGap: 12,
            rowGap: 12,
            columnSizes: [1.fr, 1.fr, 1.fr, 1.fr],
            rowSizes: [240.px, 1.fr],
            areas: '''
          header1 header2  header3 header4
          content content  content content
        ''',
            children: [
              VerticalTile(
                width: double.infinity,
                height: double.infinity,
                subText: "Dataset Count",
                icon: "assets/icons/folder.jpg",
                text: "${data?.datasetCount ?? 0}",
                button: "View",
                onTap: () {
                  context.go("/dataset");
                },
              ).inGridArea("header1"),
              VerticalTile(
                width: double.infinity,
                height: double.infinity,
                subText: "Annotation Count",
                icon: "assets/icons/pencil.jpg",
                text: "${data?.annotationCount ?? 0}",
              ).inGridArea("header2"),
              VerticalTile(
                width: double.infinity,
                height: double.infinity,
                subText: "Task Count",
                icon: "assets/icons/table.jpg",
                text: "${data?.taskCount ?? 0}",
              ).inGridArea("header3"),
              VerticalTile(
                width: double.infinity,
                height: double.infinity,
                subText: "Task Error Count",
                icon: "assets/icons/warning.jpg",
                text: "${data?.taskErrorCount ?? 0}",
              ).inGridArea("header4"),
            ],
          ),
        );
      },
    );
  }
}
