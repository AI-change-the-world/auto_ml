import 'package:auto_ml/modules/dataset/components/dataset_card_wrap.dart';
import 'package:auto_ml/modules/dataset/components/new_dataset_dialog.dart';
import 'package:auto_ml/modules/dataset/notifier/dataset_notifier.dart';
import 'package:auto_ml/modules/dataset/notifier/dataset_page_notifier.dart';
import 'package:auto_ml/modules/isar/dataset.dart';
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
        datasets = fakeDataset();

        Map<DatasetType, List<Dataset>> map = {
          if (data.selectedTypes.contains(DatasetType.image))
            DatasetType.image: [],
          if (data.selectedTypes.contains(DatasetType.text))
            DatasetType.text: [],
          if (data.selectedTypes.contains(DatasetType.other))
            DatasetType.other: [],
          if (data.selectedTypes.contains(DatasetType.audio))
            DatasetType.audio: [],
          if (data.selectedTypes.contains(DatasetType.video))
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
    return Column(
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
                                    i == pageState ? Colors.black : Colors.grey,
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
                          ref.read(datasetPageProvider.notifier).changePage(i);
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
                      );
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
          child: PageView(
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
        ),
      ],
    );
  }
}
