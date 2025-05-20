import 'package:auto_ml/api.dart';
import 'package:auto_ml/common/base_response.dart';
import 'package:auto_ml/common/dialog_wrapper.dart';
import 'package:auto_ml/i18n/strings.g.dart';
import 'package:auto_ml/modules/dataset/components/append_annotation_files_dialog.dart';
import 'package:auto_ml/modules/dataset/components/modify_annotation_classes_dialog.dart';
import 'package:auto_ml/modules/dataset/constants.dart';
import 'package:auto_ml/modules/dataset/models/annotation_list_response.dart';
import 'package:auto_ml/modules/dataset/notifier/annotation_notifier.dart';
import 'package:auto_ml/modules/dataset/notifier/dataset_notifier.dart';
import 'package:auto_ml/modules/task/components/new_train_task_dialog.dart';
import 'package:auto_ml/modules/task/models/new_training_task_request.dart';
import 'package:auto_ml/utils/dio_instance.dart';
import 'package:auto_ml/utils/styles.dart';
import 'package:auto_ml/utils/toast_utils.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:data_table_2/data_table_2.dart';
import 'package:markdown_widget/markdown_widget.dart';

class AnnotationsList extends ConsumerStatefulWidget {
  const AnnotationsList({super.key});

  @override
  ConsumerState<AnnotationsList> createState() => _AnnotationsListState();
}

class _AnnotationsListState extends ConsumerState<AnnotationsList> {
  @override
  void initState() {
    super.initState();

    WidgetsBinding.instance.addPostFrameCallback((_) {
      ref.read(annotationListProvider.notifier).updateData();
    });
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(annotationListProvider);

    return state.when(
      data: (data) {
        final current = ref.read(datasetNotifierProvider).value?.current;
        if (current == null) {
          return Center(
            child: Text(
              t.dataset_screen.dataset_no_selected,
              style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
            ),
          );
        }

        return Padding(
          padding: EdgeInsets.all(10),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.start,
            crossAxisAlignment: CrossAxisAlignment.start,
            spacing: 10,
            children: [
              Expanded(
                child: DataTable2(
                  empty: Center(
                    child: Text(t.annotation_screen.list_widget.no_data),
                  ),
                  columnSpacing: 10,
                  headingRowDecoration: BoxDecoration(
                    color: Colors.grey.shade200,
                  ),
                  columns: columns,
                  rows: getRows(data.annotations),
                ),
              ),
            ],
          ),
        );
      },
      error: (e, s) {
        return Center(child: Text(e.toString()));
      },
      loading: () => Center(child: CircularProgressIndicator()),
    );
  }

  late List<DataColumn> columns = [
    DataColumn2(
      label: Text(
        t.dataset_screen.table.annotation.id,
        style: defaultTextStyle2,
      ),
      fixedWidth: 40,
    ),
    DataColumn2(
      label: Text(
        t.dataset_screen.table.annotation.path,
        style: defaultTextStyle2,
      ),
      size: ColumnSize.L,
    ),
    DataColumn2(
      label: Text(
        t.dataset_screen.table.annotation.type,
        style: defaultTextStyle2,
      ),
      fixedWidth: 100,
    ),
    DataColumn2(
      label: Text(t.table.createat, style: defaultTextStyle2),
      size: ColumnSize.M,
    ),
    DataColumn2(
      label: Text(t.table.updateat, style: defaultTextStyle2),
      size: ColumnSize.M,
    ),
    DataColumn2(
      label: Text(t.table.operation, style: defaultTextStyle2),
      fixedWidth: 120,
    ),
  ];

  List<DataRow> getRows(List<Annotation> annotations) {
    return annotations.map((annotation) {
      return DataRow(
        cells: [
          DataCell(Text(annotation.id.toString(), style: defaultTextStyle)),
          DataCell(
            Tooltip(
              message: annotation.annotationSavePath.toString(),
              child: Text(
                annotation.annotationSavePath.toString(),
                style: defaultTextStyle,
                maxLines: 1,
                softWrap: true,
                overflow: TextOverflow.ellipsis,
              ),
            ),
          ),
          DataCell(
            Text(
              datasetTaskGetById(annotation.annotationType).name,
              style: defaultTextStyle,
            ),
          ),
          DataCell(
            Text(
              annotation.createdAt.toString().split(".").first,
              style: defaultTextStyle,
            ),
          ),
          DataCell(
            Text(
              annotation.updatedAt.toString().split(".").first,
              style: defaultTextStyle,
            ),
          ),
          DataCell(
            Row(
              spacing: 10,
              children: [
                InkWell(
                  onTap: () {
                    showGeneralDialog(
                      context: context,
                      barrierColor: Styles.barriarColor,
                      barrierDismissible: true,
                      barrierLabel: "AppendAnntationFilesDialog",
                      pageBuilder: (c, _, __) {
                        return Center(
                          child: AppendAnntationFilesDialog(
                            annotationId: annotation.id,
                          ),
                        );
                      },
                    );
                  },
                  child: Tooltip(
                    message: t.dataset_screen.table.upload_annotation,
                    child: Icon(Icons.upload, size: Styles.datatableIconSize),
                  ),
                ),
                InkWell(
                  onTap: () async {
                    if (annotation.annotationType != 1) {
                      ToastUtils.info(
                        null,
                        title: t.dataset_screen.table.support_error,
                      );
                      return;
                    }

                    DioClient().instance
                        .post(
                          Api.annotationDataset,
                          data: {
                            "datasetId": annotation.datasetId,
                            "annotationId": annotation.id,
                            // TODO: agentId
                            "agentId": 7,
                          },
                        )
                        .then((v) {
                          final BaseResponse<dynamic> bs =
                              BaseResponse<dynamic>.fromJson(v.data, (d) {});
                          ToastUtils.info(
                            null,
                            title: bs.message ?? t.global.errors.basic_error,
                          );
                        });
                  },
                  child: Tooltip(
                    message: t.dataset_screen.table.auto_annotate,
                    child: Icon(
                      Icons.square_outlined,
                      size: Styles.datatableIconSize,
                    ),
                  ),
                ),
                InkWell(
                  onTap: () {
                    if (annotation.annotationType != 0 &&
                        annotation.annotationType != 1) {
                      ToastUtils.info(
                        context,
                        title: t.dataset_screen.table.train_support_error,
                      );
                      return;
                    }

                    showGeneralDialog(
                      context: context,
                      barrierColor: Styles.barriarColor,
                      barrierDismissible: true,
                      barrierLabel: "NewTrainTaskDialog",
                      pageBuilder: (c, _, __) {
                        return Center(
                          child: NewTrainTaskDialog(
                            typeId: annotation.annotationType,
                          ),
                        );
                      },
                    ).then((v) {
                      if (v != null && v is Map<String, dynamic>) {
                        v['annotationId'] = annotation.id;
                        v['datasetId'] = annotation.datasetId;

                        NewTrainingTaskRequest request =
                            NewTrainingTaskRequest.fromJson(v);

                        // print(request);

                        DioClient().instance
                            .post(Api.newTrainTask, data: request.toJson())
                            .then((v) {
                              if (v.statusCode == 200) {
                                ToastUtils.success(
                                  null,
                                  title: t.global.errors.create_error,
                                );
                              } else {
                                ToastUtils.error(
                                  null,
                                  title: t.global.success.create_success,
                                );
                              }
                            });
                      }
                    });
                  },
                  child: Tooltip(
                    message: t.dataset_screen.table.train,
                    child: Icon(
                      Icons.work_outline_outlined,
                      size: Styles.datatableIconSize,
                    ),
                  ),
                ),
                InkWell(
                  onTap: () async {
                    if (annotation.annotationType != 3) {
                      showGeneralDialog(
                        barrierColor: Styles.barriarColor,
                        barrierDismissible: true,
                        barrierLabel: "ModifyAnnotationClassesDialog",
                        context: context,
                        pageBuilder: (c, _, __) {
                          return Center(
                            child: ModifyAnnotationClassesDialog(
                              annotationString: annotation.classItems ?? "",
                            ),
                          );
                        },
                      ).then((v) {
                        if (v != null) {
                          Map<String, dynamic> map = {
                            "id": annotation.id,
                            "classes": v,
                          };

                          DioClient().instance
                              .post(Api.annotationClassesUpdate, data: map)
                              .then((v) {
                                if (v.statusCode == 200) {
                                  ToastUtils.success(
                                    null,
                                    title: t.global.success.modify_success,
                                  );
                                  ref
                                      .read(annotationListProvider.notifier)
                                      .updateData();
                                } else {
                                  ToastUtils.error(
                                    null,
                                    title: t.global.errors.modify_error,
                                  );
                                }
                              });
                        }
                      });
                    } else {
                      showGeneralDialog(
                        barrierColor: Styles.barriarColor,
                        barrierDismissible: true,
                        barrierLabel: "ModifyAnnotationClassesDialog",
                        context: context,
                        pageBuilder: (c, _, __) {
                          return Center(
                            child: dialogWrapper(
                              width: 400,
                              height: 400,
                              child: Container(
                                padding: EdgeInsets.all(10),
                                child: MarkdownWidget(
                                  data:
                                      annotation.prompt ??
                                      t.dataset_screen.table.prompt_unset,
                                ),
                              ),
                            ),
                          );
                        },
                      );
                    }
                  },
                  child: Tooltip(
                    message:
                        annotation.annotationType == 3
                            ? t.dataset_screen.table.prompt
                            : t.dataset_screen.table.classes,
                    child: Icon(
                      annotation.annotationType == 3
                          ? Icons.text_format
                          : Icons.class_outlined,
                      size: Styles.datatableIconSize,
                    ),
                  ),
                ),
              ],
            ),
          ),
        ],
      );
    }).toList();
  }

  TextStyle defaultTextStyle = TextStyle(fontSize: 12);
  late TextStyle defaultTextStyle2 = Styles.defaultButtonTextStyle;
}
