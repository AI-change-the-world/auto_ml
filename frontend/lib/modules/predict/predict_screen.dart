import 'package:auto_ml/i18n/strings.g.dart';
import 'package:auto_ml/modules/predict/components/data_preview_dialog.dart';
import 'package:auto_ml/modules/predict/components/image_preview_dialog.dart';
import 'package:auto_ml/modules/predict/notifier/predict_data_notifier.dart';
import 'package:auto_ml/utils/conversion_util.dart';
import 'package:auto_ml/utils/styles.dart';
import 'package:data_table_2/data_table_2.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class PredictScreen extends ConsumerStatefulWidget {
  const PredictScreen({super.key});

  @override
  ConsumerState<PredictScreen> createState() => _PredictScreenState();
}

class _PredictScreenState extends ConsumerState<PredictScreen> {
  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.all(10),
      child: Column(
        spacing: 10,
        children: [
          SizedBox(
            height: 30,
            child: Row(
              children: [
                Spacer(),
                ElevatedButton(
                  style: Styles.getDefaultButtonStyle(width: 80),
                  onPressed: () {},
                  child: Text(
                    t.predict_screen.upload,
                    style: Styles.defaultButtonTextStyle,
                  ),
                ),
              ],
            ),
          ),
          Expanded(
            child: Builder(
              builder: (c) {
                final state = ref.watch(predictDataProvider);
                return state.when(
                  data: (data) {
                    return DataTable2(
                      empty: Center(
                        child: Text(t.annotation_screen.list_widget.no_data),
                      ),
                      columnSpacing: 10,
                      headingRowDecoration: BoxDecoration(
                        color: Theme.of(context).primaryColorLight,
                      ),
                      columns: columns,
                      rows:
                          data.data.map((e) {
                            return DataRow(
                              cells: [
                                DataCell(Text(e.id.toString())),
                                DataCell(Text(e.fileName)),
                                DataCell(Text(datatypeToString(e.dataType))),
                                DataCell(
                                  Text(
                                    e.createdAt.toString().split(".").first,
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
                                            barrierDismissible: true,
                                            barrierLabel: "DataPreviewDialog",
                                            barrierColor: Styles.barriarColor,
                                            pageBuilder: (c, _, _) {
                                              return Center(
                                                child: DataPreviewDialog(
                                                  fileId: e.id,
                                                  fileType: e.dataType,
                                                ),
                                              );
                                            },
                                          );
                                        },
                                        child: Icon(
                                          Icons.visibility,
                                          size: Styles.datatableIconSize,
                                        ),
                                      ),
                                      InkWell(
                                        onTap: () {
                                          // ToastUtils.info(
                                          //   context,
                                          //   title:
                                          //       "This feature is under development",
                                          // );
                                          showGeneralDialog(
                                            context: context,
                                            barrierColor: Styles.barriarColor,
                                            barrierDismissible: true,
                                            barrierLabel: "ImagePreviewDialog",
                                            pageBuilder: (c, _, _) {
                                              return Center(
                                                child: ImagePreviewDialog(
                                                  fileId: e.id,
                                                ),
                                              );
                                            },
                                          );
                                        },
                                        child: Icon(
                                          Icons.model_training,
                                          size: Styles.datatableIconSize,
                                        ),
                                      ),
                                    ],
                                  ),
                                ),
                              ],
                            );
                          }).toList(),
                    );
                  },
                  error: (e, s) {
                    return Center(child: Text(e.toString()));
                  },
                  loading: () {
                    return Center(child: CircularProgressIndicator());
                  },
                );
              },
            ),
          ),
        ],
      ),
    );
  }

  TextStyle defaultTextStyle = TextStyle(fontSize: 12);
  TextStyle defaultTextStyle2 = TextStyle(
    fontSize: 12,
    fontWeight: FontWeight.bold,
  );

  List<DataColumn2> get columns => [
    DataColumn2(
      label: Text(t.predict_screen.id, style: defaultTextStyle2),
      fixedWidth: 40,
    ),
    DataColumn2(
      label: Text(t.predict_screen.name, style: defaultTextStyle2),
      size: ColumnSize.L,
    ),
    DataColumn2(
      label: Text(t.predict_screen.type, style: defaultTextStyle2),
      size: ColumnSize.S,
    ),
    DataColumn2(
      label: Text(t.predict_screen.uploaded, style: defaultTextStyle2),
      size: ColumnSize.M,
    ),
    DataColumn2(
      label: Text(t.table.operation, style: defaultTextStyle2),
      fixedWidth: 120,
    ),
  ];
}
