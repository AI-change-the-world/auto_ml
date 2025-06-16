import 'package:auto_ml/i18n/strings.g.dart';
import 'package:auto_ml/modules/task/components/task_item_widget.dart';
import 'package:auto_ml/modules/task/notifier/task_notifier.dart';
import 'package:auto_ml/utils/styles.dart';
import 'package:data_table_2/data_table_2.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class TaskScreen extends ConsumerStatefulWidget {
  const TaskScreen({super.key});

  @override
  ConsumerState<TaskScreen> createState() => _TaskScreenState();
}

class _TaskScreenState extends ConsumerState<TaskScreen> {
  @override
  Widget build(BuildContext context) {
    final state = ref.watch(taskNotifierProvider);

    return Scaffold(
      drawerScrimColor: Colors.transparent,
      key: TaskDrawer.scaffoldKey,
      onEndDrawerChanged: (isOpened) {
        if (!isOpened) {
          ref.read(taskNotifierProvider.notifier).changeCurrent(null);
        }
      },
      endDrawer: TaskItemWidget(),
      body: Padding(
        padding: const EdgeInsets.all(10.0),
        child: Column(
          spacing: 10,
          children: [
            SizedBox(
              height: 30,
              child: Row(
                children: [
                  Spacer(),
                  ElevatedButton(
                    style: Styles.getDefaultButtonStyle(),
                    onPressed: () {},
                    child: Text(
                      t.refresh,
                      style: Styles.defaultButtonTextStyle,
                    ),
                  ),
                ],
              ),
            ),

            Expanded(
              child: state.when(
                loading: () => const Center(child: CircularProgressIndicator()),
                error:
                    (err, stack) =>
                        Center(child: Center(child: Text("Error: $err"))),
                data: (data) {
                  int totolPages =
                      data.total % 10 == 0
                          ? data.total ~/ data.pageSize
                          : data.total ~/ data.pageSize + 1;

                  return Column(
                    spacing: 10,
                    children: [
                      Expanded(
                        child: DataTable2(
                          headingRowDecoration: BoxDecoration(
                            color: Theme.of(context).primaryColorLight,
                          ),
                          columns: columns,
                          rows:
                              data.tasks.map((e) {
                                return DataRow2(
                                  cells: [
                                    DataCell(
                                      Text(
                                        e.taskId.toString(),
                                        style:
                                            Styles.defaultButtonTextStyleNormal,
                                      ),
                                    ),
                                    DataCell(
                                      Text(
                                        e.taskType,
                                        style:
                                            Styles.defaultButtonTextStyleNormal,
                                      ),
                                    ),
                                    DataCell(
                                      Text(
                                        e.datasetId.toString(),
                                        style:
                                            Styles.defaultButtonTextStyleNormal,
                                      ),
                                    ),
                                    DataCell(
                                      Text(
                                        e.annotationId.toString(),
                                        style:
                                            Styles.defaultButtonTextStyleNormal,
                                      ),
                                    ),
                                    DataCell(
                                      Text(
                                        e.createdAt
                                            .split(".")
                                            .first
                                            .replaceAll("T", " "),
                                        style:
                                            Styles.defaultButtonTextStyleNormal,
                                      ),
                                    ),
                                    DataCell(
                                      Text(
                                        e.updatedAt
                                            .split(".")
                                            .first
                                            .replaceAll("T", " "),
                                        style:
                                            Styles.defaultButtonTextStyleNormal,
                                      ),
                                    ),
                                    DataCell(
                                      Row(
                                        spacing: 10,
                                        children: [
                                          InkWell(
                                            onTap: () {
                                              ref
                                                  .read(
                                                    taskNotifierProvider
                                                        .notifier,
                                                  )
                                                  .changeCurrent(e);

                                              TaskDrawer.showDrawer();
                                            },
                                            child: Icon(
                                              Icons.details,
                                              size: Styles.datatableIconSize,
                                            ),
                                          ),
                                          // TODO
                                          InkWell(
                                            onTap: () {},
                                            child: Icon(
                                              Icons.restart_alt,
                                              size: Styles.datatableIconSize,
                                            ),
                                          ),
                                        ],
                                      ),
                                    ),
                                  ],
                                );
                              }).toList(),
                        ),
                      ),
                      SizedBox(
                        height: 30,
                        child: Row(
                          mainAxisAlignment: MainAxisAlignment.center,
                          spacing: 20,
                          children: [
                            TextButton(
                              onPressed: () {
                                ref
                                    .read(taskNotifierProvider.notifier)
                                    .prevPage();
                              },
                              child: Text(
                                'Previous',
                                style: Styles.defaultButtonTextStyle,
                              ),
                            ),

                            TextButton(
                              onPressed: () {
                                ref
                                    .read(taskNotifierProvider.notifier)
                                    .nextPage(totolPages);
                              },
                              child: Text(
                                'Next',
                                style: Styles.defaultButtonTextStyle,
                              ),
                            ),
                            Text(
                              "Page ${data.pageId} of $totolPages",
                              style: Styles.defaultButtonTextStyle,
                            ),
                          ],
                        ),
                      ),
                    ],
                  );
                },
              ),
            ),
          ],
        ),
      ),
    );
  }

  late List<DataColumn> columns = [
    DataColumn2(
      size: ColumnSize.S,
      label: Text(t.task_screen.id, style: Styles.defaultButtonTextStyle),
    ),
    DataColumn2(
      size: ColumnSize.M,
      label: Text(t.task_screen.type, style: Styles.defaultButtonTextStyle),
    ),
    DataColumn2(
      size: ColumnSize.M,
      label: Text(
        t.task_screen.dataset_id,
        style: Styles.defaultButtonTextStyle,
      ),
    ),
    DataColumn2(
      size: ColumnSize.S,
      label: Text(
        t.task_screen.annotation_id,
        style: Styles.defaultButtonTextStyle,
      ),
    ),
    DataColumn2(
      size: ColumnSize.M,
      label: Text(t.table.createat, style: Styles.defaultButtonTextStyle),
    ),
    DataColumn2(
      size: ColumnSize.M,
      label: Text(t.table.updateat, style: Styles.defaultButtonTextStyle),
    ),
    DataColumn2(
      size: ColumnSize.M,
      label: Text(t.table.operation, style: Styles.defaultButtonTextStyle),
    ),
  ];
}
