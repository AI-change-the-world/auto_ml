import 'package:auto_ml/api.dart';
import 'package:auto_ml/common/base_response.dart';
import 'package:auto_ml/i18n/strings.g.dart';
import 'package:auto_ml/modules/aether_agent/components/flow/create_new_flow_dialog.dart';
import 'package:auto_ml/modules/aether_agent/components/pipeline_preview_dialog.dart';
import 'package:auto_ml/modules/aether_agent/components/pipeline_workflow_dialog.dart';
import 'package:auto_ml/modules/aether_agent/models/agent_response.dart';
import 'package:auto_ml/modules/aether_agent/notifier/agent_notifier.dart';
import 'package:auto_ml/utils/dio_instance.dart';
import 'package:auto_ml/utils/logger.dart';
import 'package:auto_ml/utils/styles.dart';
import 'package:auto_ml/utils/toast_utils.dart';
import 'package:data_table_2/data_table_2.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class AetherAgentScreen extends ConsumerStatefulWidget {
  const AetherAgentScreen({super.key});

  @override
  ConsumerState<AetherAgentScreen> createState() => _AetherAgentScreenState();
}

class _AetherAgentScreenState extends ConsumerState<AetherAgentScreen> {
  @override
  Widget build(BuildContext context) {
    final state = ref.watch(agentProvider);

    return Container(
      padding: EdgeInsets.all(10),
      child: Column(
        spacing: 10,
        children: [
          SizedBox(
            height: 30,
            child: Row(
              spacing: 10,
              children: [
                Spacer(),
                ElevatedButton(
                  style: Styles.getDefaultButtonStyle(),
                  onPressed: () {
                    showGeneralDialog(
                      barrierColor: Styles.barriarColor,
                      barrierDismissible: true,
                      barrierLabel: 'CreateNewFlowDialog',
                      // ignore: use_build_context_synchronously
                      context: context,
                      pageBuilder: (c, _, _) {
                        return Center(child: CreateNewFlowDialog());
                      },
                    );
                  },
                  child: Text("Create", style: Styles.defaultButtonTextStyle),
                ),
                ElevatedButton(
                  style: Styles.getDefaultButtonStyle(),
                  onPressed: () {},
                  child: Text(t.refresh, style: Styles.defaultButtonTextStyle),
                ),
              ],
            ),
          ),
          Expanded(
            child: state.when(
              data: (data) {
                int totolPages =
                    data.total % 10 == 0
                        ? data.total ~/ data.pageSize
                        : data.total ~/ data.pageSize + 1;
                return Column(
                  spacing: 10,
                  children: [
                    Expanded(
                      child: DataTable2(
                        empty: Center(child: Text("No available agents")),
                        columnSpacing: 10,
                        headingRowDecoration: BoxDecoration(
                          color: Theme.of(context).primaryColorLight,
                        ),
                        columns: columns,
                        rows: getRows(data.agents),
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
                            "Page ${data.pageId} of $totolPages",
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
      label: Text(t.agent_screen.id, style: Styles.defaultButtonTextStyle),
      fixedWidth: 40,
    ),
    DataColumn2(
      label: Text(t.agent_screen.name, style: Styles.defaultButtonTextStyle),
      size: ColumnSize.S,
    ),
    DataColumn2(
      label: Text(
        t.agent_screen.description,
        style: Styles.defaultButtonTextStyle,
      ),
      size: ColumnSize.L,
    ),
    DataColumn2(
      label: Text(t.agent_screen.module, style: Styles.defaultButtonTextStyle),
      size: ColumnSize.S,
    ),
    // DataColumn2(
    //   label: Text(
    //     t.agent_screen.recommend,
    //     style: Styles.defaultButtonTextStyle,
    //   ),
    //   size: ColumnSize.S,
    // ),
    DataColumn2(
      label: Text(t.table.createat, style: Styles.defaultButtonTextStyle),
      size: ColumnSize.M,
    ),
    DataColumn2(
      label: Text(t.table.updateat, style: Styles.defaultButtonTextStyle),
      size: ColumnSize.M,
    ),
    DataColumn2(
      label: Text(t.table.operation, style: Styles.defaultButtonTextStyle),
      fixedWidth: 120,
    ),
  ];

  List<DataRow> getRows(List<Agent> agents) {
    return agents.map((agent) {
      return DataRow2(
        cells: [
          DataCell(
            Text(
              agent.id.toString(),
              style: Styles.defaultButtonTextStyleNormal,
            ),
          ),
          DataCell(
            Text(agent.name, style: Styles.defaultButtonTextStyleNormal),
          ),
          DataCell(
            Tooltip(
              message: agent.description ?? "",
              child: Text(
                agent.description ?? "",
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: Styles.defaultButtonTextStyleNormal,
              ),
            ),
          ),
          DataCell(
            Text(agent.module, style: Styles.defaultButtonTextStyleNormal),
          ),

          // DataCell(
          //   Row(
          //     spacing: 5,
          //     children: [
          //       Icon(
          //         agent.isRecommended == 1 ? Icons.check : Icons.error,
          //         size: Styles.datatableIconSize,
          //         color: agent.isRecommended == 1 ? Colors.green : Colors.amber,
          //       ),
          //       Text(
          //         agent.isRecommended == 1 ? "Recommended" : "Not recommended",
          //         style: Styles.defaultButtonTextStyleNormal,
          //       ),
          //     ],
          //   ),
          // ),
          DataCell(
            Text(
              agent.createdAt.toString().split(".").first.replaceAll("T", " "),
              style: Styles.defaultButtonTextStyleNormal,
            ),
          ),
          DataCell(
            Text(
              agent.updatedAt.toString().split(".").first.replaceAll("T", " "),
              style: Styles.defaultButtonTextStyleNormal,
            ),
          ),
          DataCell(
            Row(
              spacing: 5,
              children: [
                InkWell(
                  onTap: () {
                    if (agent.pipelineContent != null) {
                      showGeneralDialog(
                        barrierColor: Styles.barriarColor,
                        barrierDismissible: true,
                        barrierLabel: "PipelinePreviewDialog",
                        context: context,
                        pageBuilder: (c, _, _) {
                          return Center(
                            child: PipelinePreviewDialog(
                              content: agent.pipelineContent!,
                            ),
                          );
                        },
                      );
                    }
                  },
                  child: Tooltip(
                    message: "View pipeline content",
                    child: Icon(Icons.preview, size: Styles.datatableIconSize),
                  ),
                ),
                InkWell(
                  onTap: () async {
                    if (agent.pipelineContent != null) {
                      try {
                        final response = await DioClient().instance.get(
                          Api.agentWorkflowContent.replaceAll(
                            "{id}",
                            agent.id.toString(),
                          ),
                        );
                        BaseResponse<String> baseResponse =
                            BaseResponse.fromJson(
                              response.data,
                              (j) => j.toString(),
                            );
                        if (baseResponse.data != null) {
                          showGeneralDialog(
                            barrierColor: Styles.barriarColor,
                            barrierDismissible: true,
                            barrierLabel: 'PipelineWorkflowDialog',
                            // ignore: use_build_context_synchronously
                            context: context,
                            pageBuilder: (c, _, _) {
                              return Center(
                                child: PipelineWorkflowDialog(
                                  content: baseResponse.data!,
                                ),
                              );
                            },
                          );
                        } else {
                          ToastUtils.error(
                            null,
                            title: "Get workflow content is empty",
                          );
                        }
                      } catch (e, s) {
                        ToastUtils.error(
                          null,
                          title: "Get workflow content error",
                        );
                        logger.e(e);
                        logger.e(s);
                      }
                    }
                  },
                  child: Tooltip(
                    message: "View workflow",
                    child: Icon(
                      Icons.poll_outlined,
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
}
