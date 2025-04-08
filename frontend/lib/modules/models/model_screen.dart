import 'package:auto_ml/modules/isar/model.dart';
import 'package:auto_ml/modules/models/notifier/model_notifier.dart';
import 'package:auto_ml/modules/models/notifier/model_page_notifier.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
// ignore: depend_on_referenced_packages
import 'package:collection/collection.dart';

class ModelScreen extends ConsumerStatefulWidget {
  const ModelScreen({super.key});

  @override
  ConsumerState<ModelScreen> createState() => _ModelScreenState();
}

class _ModelScreenState extends ConsumerState<ModelScreen> {
  @override
  Widget build(BuildContext context) {
    final state = ref.watch(modelNotifierProvider);

    return state.when(
      data: (data) {
        var datasets = data.models;

        Map<ModelType, List<Model>> map = {
          ModelType.llm: [],
          ModelType.mllm: [],
          ModelType.vision: [],
        };

        for (var dataset in datasets) {
          map[dataset.modelType]?.add(dataset);
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
  final Map<ModelType, List<Model>> map;
  static const Color color = Color.fromARGB(255, 118, 156, 222);

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final pageState = ref.watch(modelPageNotifierProvider);
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
                          ref
                              .read(modelPageNotifierProvider.notifier)
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
                    onTap: () async {},
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
            controller: ref.read(modelPageNotifierProvider.notifier).controller,
            children: [Container(), Container(), Container()],
          ),
        ),
      ],
    );
  }
}
