import 'dart:convert';

import 'package:auto_ml/modules/task/models/task_log_response.dart';
import 'package:auto_ml/utils/logger.dart';
import 'package:auto_ml/utils/styles.dart';
import 'package:flutter/widgets.dart';
import 'package:community_charts_flutter2/community_charts_flutter2.dart'
    as charts;

class TaskLogMerged {
  final String step;
  final List<String> contents;
  final String createdAt;

  TaskLogMerged({
    required this.step,
    required this.contents,
    required this.createdAt,
  });

  Widget toWidget() {
    if (contents.length == 1 && !contents[0].contains("loss")) {
      return Text(contents[0], style: TextStyle(fontSize: 12));
    } else {
      final List<Map> data = contents.map((e) => jsonDecode(e) as Map).toList();

      return SizedBox(
        height: 300,
        width: 400,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text("Loss", style: Styles.defaultButtonTextStyle),
            AspectRatio(
              aspectRatio: 16 / 9,
              child: charts.LineChart([
                charts.Series<Map, double>(
                  id: 'losses',
                  colorFn: (_, __) => charts.MaterialPalette.blue.shadeDefault,
                  domainFn: (Map d, _) => d['epoch'] ?? 0,
                  measureFn: (Map d, _) => d['loss'] ?? 0,
                  data: data,
                ),
              ]),
            ),
          ],
        ),
      );
    }
  }
}

class TaskLogMergedList {
  final List<TaskLogMerged> logs;

  TaskLogMergedList({required this.logs});

  factory TaskLogMergedList.fromTaskLogList(List<TaskLog> logs) {
    List<TaskLogMerged> merged = [];
    for (int i = 0; i < logs.length; i++) {
      var log = logs[i];
      if (log.logContent == null) {
        continue;
      }
      if (log.logContent!.startsWith("[pre-")) {
        final str = log.logContent!.substring(
          0,
          log.logContent!.indexOf("]") + 1,
        );
        merged.add(
          TaskLogMerged(
            step: str.replaceAll("[", "").replaceAll("]", ""),
            contents: [log.logContent!.replaceFirst(str, "")],
            createdAt: log.createdAt.split(".").first.replaceAll("T", " "),
          ),
        );
      } else if (log.logContent!.startsWith("[post")) {
        final str = log.logContent!.substring(
          0,
          log.logContent!.indexOf("]") + 1,
        );
        merged.add(
          TaskLogMerged(
            step: str.replaceAll("[", "").replaceAll("]", ""),
            contents: [log.logContent!.replaceFirst(str, "")],
            createdAt: log.createdAt.split(".").first.replaceAll("T", " "),
          ),
        );
      } else {
        try {
          final jsonString = log.logContent!.replaceAllMapped(
            RegExp(r"'([^']*)'"),
            (match) {
              return '"${match[1]}"';
            },
          );
          final Map<String, dynamic> jsonMap = jsonDecode(jsonString);

          // 提取 loss 中的数字部分（使用正则）
          final lossStr = jsonMap['loss'] as String;
          final lossMatch = RegExp(r'tensor\(([\d.]+)').firstMatch(lossStr);

          final result = {
            'epoch': jsonMap['epoch'],
            'loss':
                lossMatch != null ? double.parse(lossMatch.group(1)!) : null,
          };
          if (merged.isNotEmpty &&
              merged.last.contents.isNotEmpty &&
              merged.last.contents.first.contains("epoch") &&
              merged.last.contents.first.contains("loss")) {
            merged.last.contents.add(jsonEncode(result));
          } else {
            merged.add(
              TaskLogMerged(
                step: "training",
                contents: [jsonEncode(result)],
                createdAt: log.createdAt.split(".").first.replaceAll("T", " "),
              ),
            );
          }
        } catch (e) {
          logger.e(e);
          final str = log.logContent!.substring(
            0,
            log.logContent!.indexOf("]") + 1,
          );
          merged.add(
            TaskLogMerged(
              step: str.replaceAll("[", "").replaceAll("]", ""),
              contents: [log.logContent!],
              createdAt: log.createdAt.split(".").first.replaceAll("T", " "),
            ),
          );
        }
      }
    }

    return TaskLogMergedList(logs: merged);
  }
}
