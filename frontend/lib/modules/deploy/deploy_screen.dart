import 'package:auto_ml/modules/deploy/components/predict_single_image_dialog.dart';
import 'package:auto_ml/modules/deploy/models/available_models_response.dart';
import 'package:auto_ml/modules/deploy/notifier/deploy_notifier.dart';
import 'package:auto_ml/utils/styles.dart';
import 'package:data_table_2/data_table_2.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class DeployScreen extends ConsumerStatefulWidget {
  const DeployScreen({super.key});

  @override
  ConsumerState<DeployScreen> createState() => _DeployScreenState();
}

class _DeployScreenState extends ConsumerState<DeployScreen> {
  @override
  Widget build(BuildContext context) {
    final state = ref.watch(deployNotifierProvider);

    return Container(
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
                  style: Styles.getDefaultButtonStyle(),
                  onPressed: () {},
                  child: Text("Refresh", style: Styles.defaultButtonTextStyle),
                ),
              ],
            ),
          ),
          Expanded(
            child: state.when(
              data: (data) {
                return Column(
                  spacing: 10,
                  children: [
                    Expanded(
                      child: DataTable2(
                        empty: Center(child: Text("No available models")),
                        columnSpacing: 10,
                        headingRowDecoration: BoxDecoration(
                          color: Colors.grey.shade200,
                        ),
                        columns: columns,
                        rows: getRows(data.models),
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
              error: (error, stackTrace) {
                return Center(
                  child: Text(
                    "Error: $error",
                    style: Styles.defaultButtonTextStyle,
                  ),
                );
              },
              loading: () => Center(child: CircularProgressIndicator()),
            ),
          ),
        ],
      ),
    );
  }

  late List<DataColumn> columns = [
    DataColumn2(
      label: Text('Id', style: Styles.defaultButtonTextStyle),
      fixedWidth: 40,
    ),
    DataColumn2(
      label: Text('Model path', style: Styles.defaultButtonTextStyle),
      size: ColumnSize.L,
    ),
    DataColumn2(
      label: Text('Base model', style: Styles.defaultButtonTextStyle),
      fixedWidth: 100,
    ),
    DataColumn2(
      label: Text('Dataset id', style: Styles.defaultButtonTextStyle),
      size: ColumnSize.S,
    ),
    DataColumn2(
      label: Text('Annotation id', style: Styles.defaultButtonTextStyle),
      size: ColumnSize.S,
    ),
    DataColumn2(
      label: Text('Epoch', style: Styles.defaultButtonTextStyle),
      fixedWidth: 60,
    ),
    DataColumn2(
      label: Text('Loss', style: Styles.defaultButtonTextStyle),
      fixedWidth: 60,
    ),
    DataColumn2(
      label: Text('Created at', style: Styles.defaultButtonTextStyle),
      size: ColumnSize.M,
    ),
    DataColumn2(
      label: Text('Updated at', style: Styles.defaultButtonTextStyle),
      size: ColumnSize.M,
    ),
    DataColumn2(
      label: Text('Status', style: Styles.defaultButtonTextStyle),
      size: ColumnSize.S,
    ),
    DataColumn2(
      label: Text('Operations', style: Styles.defaultButtonTextStyle),
      fixedWidth: 120,
    ),
  ];

  List<DataRow> getRows(List<AvailableModel> models) {
    return models.map((model) {
      return DataRow2(
        cells: [
          DataCell(
            Text(
              model.id.toString(),
              style: Styles.defaultButtonTextStyleNormal,
            ),
          ),
          DataCell(
            Text(model.savePath, style: Styles.defaultButtonTextStyleNormal),
          ),
          DataCell(
            Text(
              model.baseModelName,
              style: Styles.defaultButtonTextStyleNormal,
            ),
          ),
          DataCell(
            Text(
              model.datasetId.toString(),
              style: Styles.defaultButtonTextStyleNormal,
            ),
          ),
          DataCell(
            Text(
              model.annotationId.toString(),
              style: Styles.defaultButtonTextStyleNormal,
            ),
          ),
          DataCell(
            Text(
              model.epoch.toString(),
              style: Styles.defaultButtonTextStyleNormal,
            ),
          ),
          DataCell(
            Text(
              model.loss.toStringAsFixed(2),
              style: Styles.defaultButtonTextStyleNormal,
            ),
          ),
          DataCell(
            Text(
              model.createdAt.toString().split(".").first.replaceAll("T", " "),
              style: Styles.defaultButtonTextStyleNormal,
            ),
          ),
          DataCell(
            Text(
              model.updatedAt.toString().split(".").first.replaceAll("T", " "),
              style: Styles.defaultButtonTextStyleNormal,
            ),
          ),
          DataCell(
            Text(
              model.isOn ? "Online" : "Offline",
              style: Styles.defaultButtonTextStyleNormal,
            ),
          ),
          DataCell(
            Row(
              spacing: 5,
              children: [
                InkWell(
                  onTap: () {
                    if (model.isOn) {
                      ref
                          .read(deployNotifierProvider.notifier)
                          .stopModel(model.id);
                    } else {
                      ref
                          .read(deployNotifierProvider.notifier)
                          .startModel(model.id);
                    }
                  },
                  child: Tooltip(
                    message: model.isOn ? "Stop" : "Start",
                    child: Icon(
                      model.isOn ? Icons.stop : Icons.start,
                      size: Styles.datatableIconSize,
                    ),
                  ),
                ),
                InkWell(
                  onTap:
                      model.isOn
                          ? () {
                            showGeneralDialog(
                              context: context,
                              barrierDismissible: true,
                              barrierLabel: "PredictSingleImageDialog",
                              barrierColor: Styles.barriarColor,
                              pageBuilder: (c, _, __) {
                                return Center(
                                  child: PredictSingleImageDialog(
                                    modelId: model.id,
                                  ),
                                );
                              },
                            );
                          }
                          : null,
                  child: Tooltip(
                    message: "predict",
                    child: Icon(
                      Icons.batch_prediction,
                      size: Styles.datatableIconSize,
                      color: model.isOn ? Colors.black : Colors.grey,
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
}
