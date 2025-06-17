import 'package:auto_ml/modules/home/models/home_index_response.dart';
import 'package:auto_ml/modules/home/notifier/home_notifier.dart';
import 'package:auto_ml/modules/vertical_tile.dart';
import 'package:auto_ml/utils/logger.dart';
import 'package:flutter/material.dart';
import 'package:flutter_layout_grid/flutter_layout_grid.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:community_charts_flutter/community_charts_flutter.dart'
    as charts;
// ignore: depend_on_referenced_packages
import 'package:intl/intl.dart';

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
        List<charts.Series<TaskPerDay, String>> getData(
          List<TaskPerDay> tasks,
        ) {
          return [
            charts.Series<TaskPerDay, String>(
              // colorFn: (_, __) => charts.MaterialPalette.blue.shadeDefault,
              id: '每日任务数',
              domainFn: (TaskPerDay task, _) => task.date,
              measureFn: (TaskPerDay task, _) => task.taskCount,
              data: tasks,
              labelAccessorFn:
                  (TaskPerDay task, _) =>
                      task.taskCount == 0 ? '' : '${task.taskCount}',
            ),
            charts.Series<TaskPerDay, String>(
              // colorFn: (_, __) => charts.MaterialPalette.green.shadeDefault,
              id: '每日任务占用时间（秒）',
              domainFn: (TaskPerDay task, _) => task.date,
              measureFn: (TaskPerDay task, _) => task.taskDuration,
              data: tasks,
              labelAccessorFn:
                  (TaskPerDay task, _) =>
                      task.taskDuration == 0 ? '' : '${task.taskDuration}',
            ),
          ];
        }

        final list = getData(data?.taskPerDays ?? []);

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
                fromColor: Color.fromARGB(230, 99, 205, 218),
                toColor: Color.fromARGB(230, 143, 223, 207),
                width: double.infinity,
                height: double.infinity,
                subText: "Dataset Count",
                icon: "assets/icons/folder.png",
                text: "${data?.datasetCount ?? 0}",
                button: "View",
                onTap: () {
                  context.go("/dataset");
                },
              ).inGridArea("header1"),
              VerticalTile(
                fromColor: Color.fromARGB(230, 129, 155, 221),
                toColor: Color.fromARGB(230, 185, 194, 241),
                width: double.infinity,
                height: double.infinity,
                subText: "Annotation Count",
                icon: "assets/icons/pencil.png",
                text: "${data?.annotationCount ?? 0}",
              ).inGridArea("header2"),
              VerticalTile(
                fromColor: Color.fromARGB(230, 165, 132, 227),
                toColor: Color.fromARGB(230, 208, 166, 247),
                width: double.infinity,
                height: double.infinity,
                subText: "Task Count",
                icon: "assets/icons/table.png",
                text: "${data?.taskCount ?? 0}",
              ).inGridArea("header3"),
              VerticalTile(
                fromColor: Color.fromARGB(230, 255, 168, 142),
                toColor: Color.fromARGB(230, 255, 117, 117),
                width: double.infinity,
                height: double.infinity,
                subText: "Task Error Count",
                icon: "assets/icons/warning.png",
                text: "${data?.taskErrorCount ?? 0}",
              ).inGridArea("header4"),
              Material(
                color: Colors.white,
                borderRadius: BorderRadius.circular(20),
                elevation: 4,
                child: Padding(
                  padding: EdgeInsetsGeometry.all(10),
                  child: charts.BarChart(
                    list,
                    animate: true,
                    behaviors: [
                      charts.ChartTitle(
                        '任务统计图', // 标题文本

                        behaviorPosition: charts.BehaviorPosition.top,
                        titleOutsideJustification:
                            charts.OutsideJustification.middleDrawArea,
                        titleStyleSpec: charts.TextStyleSpec(
                          fontSize: 16,
                          fontFamily: "ph",
                        ),
                      ),
                      charts.SeriesLegend(
                        position: charts.BehaviorPosition.inside,
                        insideJustification: charts.InsideJustification.topEnd,
                        horizontalFirst: false,
                        cellPadding: EdgeInsets.only(right: 4.0, bottom: 4.0),
                        showMeasures: true,
                      ),
                    ],
                    barGroupingType: charts.BarGroupingType.grouped,
                    domainAxis: charts.OrdinalAxisSpec(
                      tickProviderSpec: charts.StaticOrdinalTickProviderSpec(
                        _generateTicks(
                          DateTime.now().subtract(Duration(days: 29)),
                          DateTime.now(),
                        ),
                      ),
                      renderSpec: charts.SmallTickRendererSpec(
                        // labelRotation: 45,
                        labelStyle: charts.TextStyleSpec(fontSize: 10),
                      ),
                    ),
                  ),
                ),
              ).inGridArea("content"),
            ],
          ),
        );
      },
    );
  }
}

/// 每10天一个 tickSpec
List<charts.TickSpec<String>> _generateTicks(
  DateTime start,
  DateTime end, {
  int intervalDays = 10,
}) {
  final ticks = <charts.TickSpec<String>>[];
  final dateFormat = DateFormat('yyyy-MM-dd');
  var current = DateTime(start.year, start.month, start.day);
  while (!current.isAfter(end)) {
    ticks.add(charts.TickSpec(dateFormat.format(current)));
    current = current.add(Duration(days: intervalDays));
  }
  ticks.add(charts.TickSpec(dateFormat.format(DateTime.now())));
  return ticks;
}
