import 'package:auto_ml/modules/task/models/task.dart';
import 'package:auto_ml/utils/conversion_util.dart' show taskTypeToString;
import 'package:flutter/material.dart';

class TaskItemWidget extends StatefulWidget {
  const TaskItemWidget({super.key, required this.task});
  final Task task;

  @override
  State<TaskItemWidget> createState() => _TaskItemWidgetState();
}

class _TaskItemWidgetState extends State<TaskItemWidget> {
  bool onHover = false;
  bool isExpanded = false;

  TextStyle defaultTextStyle = TextStyle(fontSize: 12);

  @override
  Widget build(BuildContext context) {
    return AnimatedContainer(
      duration: Duration(milliseconds: 200),
      height: isExpanded ? 300 : 30,
      decoration: BoxDecoration(
        color: onHover ? Colors.grey[100] : Colors.white,
        borderRadius: BorderRadius.circular(5),
      ),
      child: Column(
        children: [
          SizedBox(
            height: 30,
            child: GestureDetector(
              onTap: () {
                setState(() {
                  isExpanded = !isExpanded;
                });
              },
              child: MouseRegion(
                cursor: SystemMouseCursors.click,
                onEnter: (event) {
                  setState(() {
                    onHover = true;
                  });
                },
                onExit: (event) {
                  setState(() {
                    onHover = false;
                  });
                },
                child: Row(
                  children: [
                    Expanded(
                      flex: 1,
                      child: Center(
                        child: Text(
                          widget.task.taskId.toString(),
                          style: defaultTextStyle,
                        ),
                      ),
                    ),
                    Expanded(
                      flex: 2,
                      child: Center(
                        child: Text(
                          taskTypeToString(widget.task.taskType),
                          style: defaultTextStyle,
                        ),
                      ),
                    ),
                    Expanded(
                      flex: 2,
                      child: Center(
                        child: Text(
                          widget.task.datasetId.toString(),
                          style: defaultTextStyle,
                        ),
                      ),
                    ),
                    Expanded(
                      flex: 2,
                      child: Center(
                        child: Text(
                          widget.task.annotationId.toString(),
                          style: defaultTextStyle,
                        ),
                      ),
                    ),
                    Expanded(
                      flex: 2,
                      child: Center(
                        child: Text(
                          widget.task.createdAt
                              .toString()
                              .split(".")
                              .first
                              .replaceAll("T", " "),
                          style: defaultTextStyle,
                        ),
                      ),
                    ),
                    Expanded(flex: 2, child: Center(child: Row())),
                  ],
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
