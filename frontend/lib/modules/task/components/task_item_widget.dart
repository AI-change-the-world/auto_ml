import 'package:auto_ml/api.dart';
import 'package:auto_ml/common/base_response.dart';
import 'package:auto_ml/modules/task/models/task_log_response.dart';
import 'package:auto_ml/modules/task/notifier/task_notifier.dart';
import 'package:auto_ml/modules/task/utils/task_log_utils.dart';
import 'package:auto_ml/utils/dio_instance.dart';
import 'package:auto_ml/utils/logger.dart';
import 'package:auto_ml/utils/styles.dart';
import 'package:auto_ml/utils/toast_utils.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:timelines_plus/timelines_plus.dart';

class TaskItemWidget extends ConsumerStatefulWidget {
  const TaskItemWidget({super.key});

  @override
  ConsumerState<TaskItemWidget> createState() => _TaskItemWidgetState();
}

class _TaskItemWidgetState extends ConsumerState<TaskItemWidget> {
  bool onHover = false;
  bool isExpanded = false;

  TextStyle defaultTextStyle = TextStyle(fontSize: 12);

  @override
  Widget build(BuildContext context) {
    final task = ref.read(taskNotifierProvider).value?.selectedTask;

    return Container(
      decoration: BoxDecoration(color: Colors.white),
      width: MediaQuery.of(context).size.width * 0.5,
      height: double.infinity,
      child:
          task == null
              ? Center(child: CircularProgressIndicator())
              : Consumer(
                builder: (context, ref, _) {
                  final asyncDetail = ref.watch(
                    taskDetailProvider(task.taskId),
                  );
                  return asyncDetail.when(
                    data: (detail) {
                      TaskLogMergedList merged =
                          TaskLogMergedList.fromTaskLogList(detail);

                      return SingleChildScrollView(
                        padding: EdgeInsets.all(10),
                        child: FixedTimeline.tileBuilder(
                          builder: TimelineTileBuilder.connectedFromStyle(
                            contentsAlign: ContentsAlign.reverse,
                            oppositeContentsBuilder:
                                (context, index) => Padding(
                                  padding: const EdgeInsets.all(8.0),
                                  child: merged.logs[index].toWidget(),
                                ),
                            contentsBuilder:
                                (context, index) => Card(
                                  child: Padding(
                                    padding: const EdgeInsets.all(8.0),
                                    child: FittedBox(
                                      child: Column(
                                        children: [
                                          Text(
                                            merged.logs[index].step,
                                            style:
                                                Styles.defaultButtonTextStyle,
                                          ),
                                          Text(
                                            merged.logs[index].createdAt,
                                            style:
                                                Styles
                                                    .defaultButtonTextStyleNormal,
                                          ),
                                        ],
                                      ),
                                    ),
                                  ),
                                ),
                            connectorStyleBuilder:
                                (context, index) => ConnectorStyle.solidLine,
                            indicatorStyleBuilder:
                                (context, index) => IndicatorStyle.dot,
                            itemCount: merged.logs.length,
                          ),
                        ),
                      );
                    },
                    loading: () => CircularProgressIndicator(),
                    error: (e, _) => Text('Error: $e'),
                  );
                },
              ),
    );
  }
}

final taskDetailProvider = FutureProvider.family<List<TaskLog>, int>((
  ref,
  taskId,
) async {
  try {
    final response = await DioClient().instance.get(
      Api.taskLog.replaceAll("{id}", taskId.toString()),
    );
    if (response.statusCode == 200) {
      BaseResponse<TaskLogResponse> baseResponse = BaseResponse.fromJson(
        response.data,
        (j) => TaskLogResponse.fromJson({"logs": j}),
      );
      return baseResponse.data?.logs ?? [];
    } else {
      throw Exception('Failed to load task detail');
    }
  } catch (e) {
    logger.e(e);
    ToastUtils.error(null, title: "Failed to load task log");
    return [];
  }
});
