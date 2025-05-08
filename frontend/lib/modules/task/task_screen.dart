import 'package:auto_ml/modules/task/components/task_item_widget.dart';
import 'package:auto_ml/modules/task/notifier/task_notifier.dart';
import 'package:auto_ml/utils/styles.dart';
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
    return Padding(
      padding: const EdgeInsets.all(10.0),
      child: Column(
        children: [
          SizedBox(
            height: 30,
            child: Row(
              children: [
                Spacer(),
                ElevatedButton(
                  style: Styles.getDefaultButtonStyle(),
                  onPressed: () {},
                  child: Text("Refresh", style: Styles.defaultButtonTextStyle),
                ),
              ],
            ),
          ),
          SizedBox(height: 10),
          Container(
            height: 30,
            width: double.infinity,
            decoration: BoxDecoration(color: Colors.grey.shade200),
            child: Row(
              children: [
                Expanded(
                  flex: 1,
                  child: Center(
                    child: Text("Id", style: Styles.defaultButtonTextStyle),
                  ),
                ),
                Expanded(
                  flex: 2,
                  child: Center(
                    child: Text("Type", style: Styles.defaultButtonTextStyle),
                  ),
                ),
                Expanded(
                  flex: 2,
                  child: Center(
                    child: Text(
                      "Dataset Id",
                      style: Styles.defaultButtonTextStyle,
                    ),
                  ),
                ),
                Expanded(
                  flex: 2,
                  child: Center(
                    child: Text(
                      "Annotation Id",
                      style: Styles.defaultButtonTextStyle,
                    ),
                  ),
                ),
                Expanded(
                  flex: 2,
                  child: Center(
                    child: Text(
                      "Created At",
                      style: Styles.defaultButtonTextStyle,
                    ),
                  ),
                ),
                Expanded(
                  flex: 2,
                  child: Center(
                    child: Text("Status", style: Styles.defaultButtonTextStyle),
                  ),
                ),
              ],
            ),
          ),

          Expanded(
            child: Builder(
              builder: (c) {
                final state = ref.watch(taskNotifierProvider);
                return state.when(
                  loading:
                      () => const Center(child: CircularProgressIndicator()),
                  error:
                      (err, stack) =>
                          Center(child: Center(child: Text("Error: $err"))),
                  data: (data) {
                    return Column(
                      spacing: 10,
                      children: [
                        Expanded(
                          child: ListView.builder(
                            itemCount: data.tasks.length,
                            itemBuilder: (c, index) {
                              final task = data.tasks[index];
                              return TaskItemWidget(task: task);
                            },
                          ),
                        ),
                        SizedBox(
                          height: 30,
                          child: Row(
                            mainAxisAlignment: MainAxisAlignment.center,
                            spacing: 20,
                            children: [
                              TextButton(
                                onPressed: () {},
                                child: Text(
                                  'Previous',
                                  style: Styles.defaultButtonTextStyle,
                                ),
                              ),

                              TextButton(
                                onPressed: () {},
                                child: Text(
                                  'Next',
                                  style: Styles.defaultButtonTextStyle,
                                ),
                              ),
                              Text(
                                "Page ${data.pageId} of ${data.total ~/ data.pageSize + 1}",
                                style: Styles.defaultButtonTextStyle,
                              ),
                            ],
                          ),
                        ),
                      ],
                    );
                  },
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}
