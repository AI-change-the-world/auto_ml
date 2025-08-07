import 'package:auto_ml/i18n/strings.g.dart';
import 'package:auto_ml/modules/annotation/components/confirm_dialog.dart';
import 'package:auto_ml/modules/annotation/notifiers/annotation_notifier.dart';
import 'package:auto_ml/modules/current_dataset_annotation_notifier.dart';
import 'package:auto_ml/utils/logger.dart';
import 'package:auto_ml/utils/styles.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class FileList extends ConsumerWidget {
  const FileList({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final data = ref.watch(
      currentDatasetAnnotationNotifierProvider.select((state) => state.data),
    );

    logger.d("FileList: ${data.length} items");
    final current = ref.watch(
      currentDatasetAnnotationNotifierProvider.select((v) => v.currentFilePath),
    );

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
                        itemBuilder: (context, index) {
                          if (data[index].$1 == current) {
                            return _wrapper(
                              Container(
                                padding: EdgeInsets.only(left: 10),
                                decoration: BoxDecoration(
                                  color: Colors.lightBlueAccent,
                                ),
                                child: Tooltip(
                                  waitDuration: Duration(milliseconds: 500),
                                  message: data[index].$1,
                                  child: Text(
                                    data[index].$1.split("/").last,
                                    // style: TextStyle(color: Colors.white),
                                    maxLines: 1,
                                    softWrap: true,
                                    overflow: TextOverflow.ellipsis,
                                  ),
                                ),
                              ),
                              ref,
                              index,
                              context,
                              data,
                            );
                          }
                          return _wrapper(
                            Container(
                              decoration: BoxDecoration(
                                color: Colors.transparent,
                              ),
                              padding: EdgeInsets.only(left: 10),
                              child: Tooltip(
                                waitDuration: Duration(milliseconds: 500),
                                message: data[index].$1,
                                child: Text(
                                  data[index].$1.split("/").last,
                                  // style: TextStyle(color: Colors.white),
                                  maxLines: 1,
                                  softWrap: true,
                                  overflow: TextOverflow.ellipsis,
                                ),
                              ),
                            ),
                            ref,
                            index,
                            context,
                            data,
                          );
                        },
                        itemCount: data.length,
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

  Widget _wrapper(
    Widget child,
    WidgetRef ref,
    int index,
    BuildContext context,
    data,
  ) {
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
