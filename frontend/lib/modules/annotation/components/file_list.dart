import 'package:auto_ml/i18n/strings.g.dart';
import 'package:auto_ml/modules/annotation/components/confirm_dialog.dart';
import 'package:auto_ml/modules/annotation/notifiers/annotation_notifier.dart';
import 'package:auto_ml/modules/current_dataset_annotation_notifier.dart';
import 'package:auto_ml/utils/logger.dart';
import 'package:auto_ml/utils/styles.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class FileList extends ConsumerStatefulWidget {
  const FileList({super.key});

  @override
  ConsumerState<FileList> createState() => _FileListState();
}

class _FileListState extends ConsumerState<FileList> {
  @override
  Widget build(BuildContext context) {
    final data = ref.watch(
      currentDatasetAnnotationNotifierProvider.select((v) => v.data),
    );

    logger.d("FileList: ${data.length} items");

    return Material(
      borderRadius: BorderRadius.circular(10),
      color: Colors.grey[100],
      elevation: 4,
      child: Container(
        margin: EdgeInsets.only(top: 10, bottom: 10),
        width: 200,
        height: double.infinity,
        padding: EdgeInsets.all(5),
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(10),
          // color: Colors.grey[100],
          color: Colors.grey[100],
        ),
        child: Column(
          spacing: 10,
          children: [
            Text(
              t.annotation_screen.list.file_list,
              style: TextStyle(
                fontWeight: FontWeight.bold,
                color: Colors.black,
              ),
            ),
            Expanded(
              child:
                  data.isEmpty
                      ? Center(
                        child: Text(
                          t.annotation_screen.list.empty,
                          style: TextStyle(color: Colors.white),
                        ),
                      )
                      : ListView.builder(
                        itemCount: data.length,
                        itemBuilder: (context, index) {
                          final filePath = data[index].$1;

                          return Consumer(
                            builder: (context, ref, _) {
                              final current = ref.watch(
                                currentDatasetAnnotationNotifierProvider.select(
                                  (v) => v.currentFilePath,
                                ),
                              );

                              final isCurrent = filePath == current;

                              return _wrapper(
                                Container(
                                  padding: EdgeInsets.only(left: 10),
                                  decoration: BoxDecoration(
                                    color:
                                        isCurrent
                                            ? Colors.lightBlueAccent
                                            : Colors.transparent,
                                  ),
                                  child: Tooltip(
                                    waitDuration: Duration(milliseconds: 500),
                                    message: filePath,
                                    child: Text(
                                      filePath.split("/").last,
                                      maxLines: 1,
                                      softWrap: true,
                                      overflow: TextOverflow.ellipsis,
                                    ),
                                  ),
                                ),
                                index,
                                data,
                              );
                            },
                          );
                        },
                      ),
            ),
            if (ref
                    .read(currentDatasetAnnotationNotifierProvider)
                    .annotation
                    ?.annotationType !=
                1)
              SizedBox(
                height: 30,
                child: Row(
                  spacing: 10,
                  children: [
                    Spacer(),
                    TextButton(
                      onPressed: () {
                        ref
                            .read(
                              currentDatasetAnnotationNotifierProvider.notifier,
                            )
                            .prevData();
                      },
                      child: Text(
                        t.annotation_screen.list.prev,
                        style: Styles.defaultButtonTextStyle,
                      ),
                    ),
                    TextButton(
                      onPressed: () {
                        ref
                            .read(
                              currentDatasetAnnotationNotifierProvider.notifier,
                            )
                            .nextData();
                      },
                      child: Text(
                        t.annotation_screen.list.next,
                        style: Styles.defaultButtonTextStyle,
                      ),
                    ),
                  ],
                ),
              ),
          ],
        ),
      ),
    );
  }

  Widget _wrapper(Widget child, int index, data) {
    return MouseRegion(
      cursor: SystemMouseCursors.click,
      child: GestureDetector(
        onTap: () async {
          // print("a");
          if (ref.read(annotationContainerProvider).modified) {
            await showGeneralDialog(
              barrierColor: Styles.barriarColor,
              barrierDismissible: true,
              barrierLabel: 'ConfirmDialog',
              context: context,
              pageBuilder: (c, _, _) {
                return Center(
                  child: ConfirmDialog(
                    height: 80,
                    content: "Unsaved changes will be lost. Continue?",
                  ),
                );
              },
            ).then((v) {
              if (v == true) {
                ref
                    .read(currentDatasetAnnotationNotifierProvider.notifier)
                    .changeCurrentData(data[index]);
                ref
                    .read(annotationContainerProvider.notifier)
                    .changeModifiedStatus(false);

                return;
              }
            });
          } else {
            ref
                .read(currentDatasetAnnotationNotifierProvider.notifier)
                .changeCurrentData(data[index]);

            ref
                .read(annotationContainerProvider.notifier)
                .changeModifiedStatus(false);
          }
        },
        child: child,
      ),
    );
  }
}
