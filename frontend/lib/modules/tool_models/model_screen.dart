import 'package:auto_ml/modules/dataset/constants.dart';
import 'package:auto_ml/modules/tool_models/components/new_model_dialog.dart';
import 'package:auto_ml/modules/tool_models/models/tool_model_response.dart';
import 'package:auto_ml/modules/tool_models/notifier/model_notifier.dart';
import 'package:auto_ml/modules/tool_models/notifier/model_page_notifier.dart';
import 'package:auto_ml/utils/styles.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
// ignore: depend_on_referenced_packages
import 'package:collection/collection.dart';
import 'package:he/he.dart' show AnimatedTile;

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

        Map<String, List<ToolModel>> map = {};

        for (var dataset in datasets) {
          if (dataset.type != null) {
            if (map.containsKey(dataset.type)) {
              map[dataset.type]?.add(dataset);
            } else {
              map[dataset.type!] = [dataset];
            }
          } else {
            if (map.containsKey("others")) {
              map["others"]?.add(dataset);
            } else {
              map["others"] = [dataset];
            }
          }
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
  final Map<String, List<ToolModel>> map;
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
                              // entry.key.icon(
                              //   color:
                              //       i == pageState ? Colors.black : Colors.grey,
                              //   size: 16,
                              // ),
                              Text(
                                "${entry.key} (${entry.value.length})",
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
                    onTap: () async {
                      showGeneralDialog(
                        barrierColor: Styles.barriarColor,
                        barrierDismissible: true,
                        barrierLabel: "NewModelDialog",
                        context: context,
                        pageBuilder: (c, _, _) {
                          return Center(
                            child: NewModelDialog(
                              initialType: ModelType.values[pageState],
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
            controller: ref.read(modelPageNotifierProvider.notifier).controller,
            children:
                map.entries.map((v) => _ToolModelScreen(models: v)).toList(),
          ),
        ),
      ],
    );
  }
}

class _ToolModelScreen extends StatelessWidget {
  const _ToolModelScreen({required this.models});
  final MapEntry<String, List<ToolModel>> models;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.only(left: 10, right: 10),
      child: Wrap(
        spacing: 10,
        runSpacing: 10,
        children:
            models.value
                .map(
                  (v) => AnimatedTile(
                    color: Colors.lightBlueAccent,
                    title: v.name,
                    description: v.description,
                    icon: Icon(Icons.abc, color: Colors.white),
                    onTap: () {},
                  ),
                )
                .toList(),
      ),
    );
  }
}
