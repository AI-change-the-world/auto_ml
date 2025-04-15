import 'package:auto_ml/modules/dataset/components/annotations_list.dart';
import 'package:auto_ml/modules/dataset/components/dataset_card_wrap.dart';
import 'package:auto_ml/modules/dataset/components/new_dataset_dialog.dart';
import 'package:auto_ml/modules/dataset/constants.dart';
import 'package:auto_ml/modules/dataset/notifier/annotation_notifier.dart';
import 'package:auto_ml/modules/dataset/notifier/dataset_notifier.dart';
import 'package:auto_ml/modules/dataset/notifier/dataset_page_notifier.dart';
import 'package:auto_ml/modules/dataset/notifier/dataset_state.dart';
import 'package:auto_ml/modules/dataset/notifier/delete_zone_notifier.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
// ignore: depend_on_referenced_packages
import 'package:collection/collection.dart';

class DatasetScreen extends ConsumerStatefulWidget {
  const DatasetScreen({super.key});

  @override
  ConsumerState<DatasetScreen> createState() => _DatasetScreenState();
}

class _DatasetScreenState extends ConsumerState<DatasetScreen> {
  late List<DatasetType> selectedTypes = List.of(DatasetType.values);

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(datasetNotifierProvider);

    return state.when(
      data: (data) {
        var datasets = data.datasets;

        Map<DatasetType, List<Dataset>> map = {
          DatasetType.image: [],
          DatasetType.text: [],
          DatasetType.other: [],
          DatasetType.audio: [],
          DatasetType.video: [],
        };

        for (var dataset in datasets) {
          map[dataset.type]?.add(dataset);
        }

        return Padding(
          padding: EdgeInsets.only(top: 10, bottom: 10, left: 20, right: 20),
          child: _Inner(map: map),
        );
      },
      error: (error, stackTrace) {
        return Center(child: Text('Error: $error'));
      },
      loading: () {
        return Center(child: CircularProgressIndicator());
      },
    );
  }
}

class _Inner extends ConsumerWidget {
  const _Inner({required this.map});
  final Map<DatasetType, List<Dataset>> map;
  static const Color color = Color.fromARGB(255, 118, 156, 222);
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final pageState = ref.watch(datasetPageProvider);
    return Scaffold(
      drawerScrimColor: Colors.transparent,
      key: GlobalDrawer.scaffoldKey,
      endDrawer: AnnotationsList(),
      body: Column(
        children: [
          SizedBox(
            height: 35,
            child: Row(
              spacing: 10,
              children: [
                ...map.entries.mapIndexed((i, entry) {
                  return Column(
                    children: [
                      SizedBox(
                        height: 30,
                        child: InkWell(
                          borderRadius: BorderRadius.circular(4),
                          child: Ink(
                            decoration: BoxDecoration(
                              borderRadius: BorderRadius.only(
                                topLeft: Radius.circular(4),
                                topRight: Radius.circular(4),
                              ),
                            ),
                            width: 100,
                            height: 28,
                            child: Row(
                              mainAxisAlignment: MainAxisAlignment.center,
                              spacing: 5,
                              children: [
                                entry.key.icon(
                                  color:
                                      i == pageState
                                          ? Colors.black
                                          : Colors.grey,
                                  size: 16,
                                ),
                                Text(
                                  "${entry.key.name} (${entry.value.length})",
                                  style: TextStyle(
                                    fontWeight:
                                        i == pageState ? FontWeight.bold : null,
                                    color:
                                        i == pageState
                                            ? Colors.black
                                            : Colors.grey,
                                  ),
                                ),
                              ],
                            ),
                          ),
                          onTap: () {
                            ref
                                .read(datasetPageProvider.notifier)
                                .changePage(i);
                          },
                        ),
                      ),
                      Spacer(),
                      Container(
                        width: 100,
                        height: 2,
                        color: i == pageState ? color : Colors.transparent,
                      ),
                    ],
                  );
                }),
                Spacer(),
                // GestureDetector(child: Container(child: ,) Icon(Icons.add)),
                Material(
                  borderRadius: BorderRadius.circular(20),
                  child: MouseRegion(
                    cursor: SystemMouseCursors.click,
                    child: GestureDetector(
                      onTap: () async {
                        showGeneralDialog(
                          barrierColor: Colors.black.withValues(alpha: 0.1),
                          barrierDismissible: true,
                          barrierLabel: "NewDatasetDialog",
                          context: context,
                          pageBuilder: (c, _, __) {
                            return Center(
                              child: NewDatasetDialog(
                                initialType: DatasetType.values[pageState],
                              ),
                            );
                          },
                        ).then((v) {
                          if (v == null) {
                            return;
                          }
                          ref
                              .read(datasetNotifierProvider.notifier)
                              .addDataset(v as Dataset);
                        });
                      },
                      child: Container(
                        decoration: BoxDecoration(
                          color: Colors.green,
                          borderRadius: BorderRadius.circular(20),
                        ),
                        padding: EdgeInsets.all(1),
                        child: Icon(Icons.add, color: Colors.white, size: 18),
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ),
          Divider(height: 0.5),
          SizedBox(height: 10),

          Expanded(
            child: Stack(
              children: [
                PageView(
                  physics: NeverScrollableScrollPhysics(),
                  controller: ref.read(datasetPageProvider.notifier).controller,
                  children:
                      map.entries.map((entry) {
                        return DatasetCardWrap(
                          type: entry.key,
                          datasets: entry.value,
                        );
                      }).toList(),
                ),
                if (ref.watch(deleteZoneNotifierProvider))
                  Positioned(right: 10, bottom: 10, child: _DeleteZone()),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _DeleteZone extends ConsumerStatefulWidget {
  const _DeleteZone();

  @override
  ConsumerState<_DeleteZone> createState() => __DeleteZoneState();
}

class __DeleteZoneState extends ConsumerState<_DeleteZone> {
  bool onHovering = false;

  @override
  Widget build(BuildContext context) {
    return DragTarget<Dataset>(
      onWillAcceptWithDetails: (details) {
        setState(() {
          onHovering = true;
        });
        return true;
      },
      onAcceptWithDetails: (details) {
        showGeneralDialog(
          barrierColor: Colors.black.withValues(alpha: 0.1),
          barrierDismissible: true,
          barrierLabel: '_ConfirmDialog',
          context: context,
          pageBuilder: (c, _, __) {
            return Center(
              child: _ConfirmDialog(
                content: "Are you sure you want to delete this dataset?",
                title: "Delete Dataset",
              ),
            );
          },
        ).then((v) {
          if (v == true) {
            ref
                .read(datasetNotifierProvider.notifier)
                .deleteDataset(details.data.id);
          }
        });
      },
      onLeave: (data) {
        setState(() {
          onHovering = false;
        });
      },
      builder: (c, _, __) {
        return Material(
          elevation: 10,
          borderRadius: BorderRadius.circular(10),
          child: Container(
            width: 80,
            height: 80,
            decoration: BoxDecoration(borderRadius: BorderRadius.circular(10)),
            child: Center(
              child: Icon(
                Icons.delete,
                size: 40,
                color: onHovering ? Colors.red : Colors.black,
              ),
            ),
          ),
        );
      },
    );
  }
}

class _ConfirmDialog extends StatelessWidget {
  const _ConfirmDialog({required this.title, required this.content});
  final String title;
  final String content;

  @override
  Widget build(BuildContext context) {
    return Material(
      elevation: 10,
      borderRadius: BorderRadius.circular(8),
      child: Container(
        padding: EdgeInsets.all(20),
        width: 300,
        height: 150,
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(8),
        ),
        child: Column(
          spacing: 10,
          mainAxisAlignment: MainAxisAlignment.start,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              title,
              style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
            ),
            Text(content, style: const TextStyle(fontSize: 14)),
            const Spacer(),
            Row(
              mainAxisAlignment: MainAxisAlignment.end,
              children: [
                TextButton(
                  onPressed: () {
                    Navigator.of(context).pop(true);
                  },
                  child: Text("确认"),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
