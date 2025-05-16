import 'package:auto_ml/i18n/strings.g.dart';
import 'package:auto_ml/modules/dataset/components/append_dataset_files_dialog.dart';
import 'package:auto_ml/modules/dataset/notifier/dataset_file_list_notifier.dart';
import 'package:auto_ml/modules/dataset/notifier/dataset_file_state.dart';
import 'package:auto_ml/modules/dataset/notifier/dataset_notifier.dart';
import 'package:auto_ml/utils/styles.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class DatasetFileDetails extends ConsumerWidget {
  const DatasetFileDetails({super.key});

  String getStatus(int status) {
    switch (status) {
      case 0:
        return "Scanning";
      case 1:
        return "Scan complete";
      case 2:
        return "Scan failed";
      default:
        return "Others";
    }
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final dataset = ref.read(datasetNotifierProvider).value?.current;

    if (dataset == null) {
      return Center(child: Text(t.dataset_screen.files.file_details.empty));
    }

    final state = ref.watch(datasetFileListNotifierProvider);

    return state.when(
      data: (DatasetFileState data) {
        return Container(
          padding: EdgeInsets.all(10),
          child: Column(
            spacing: 10,
            children: [
              Row(
                spacing: 10,
                children: [
                  Expanded(
                    child: Row(
                      children: [
                        Text.rich(
                          TextSpan(
                            children: [
                              TextSpan(
                                text: "${t.dataset_screen.table.count}: ",
                                style: TextStyle(
                                  fontWeight: FontWeight.bold,
                                  fontSize: 12,
                                ),
                              ),
                              TextSpan(
                                text: "${data.count}",
                                style: TextStyle(fontSize: 12),
                              ),
                            ],
                          ),
                        ),
                        SizedBox(width: 10),
                        Material(
                          borderRadius: BorderRadius.circular(20),
                          child: MouseRegion(
                            cursor: SystemMouseCursors.click,
                            child: GestureDetector(
                              onTap: () async {
                                showGeneralDialog(
                                  context: context,
                                  barrierColor: Styles.barriarColor,
                                  barrierDismissible: true,
                                  barrierLabel: "AppendDatasetFilesDialog",
                                  pageBuilder: (c, _, __) {
                                    return Center(
                                      child: AppendDatasetFilesDialog(
                                        datasetType: dataset.type.index,
                                        datasetId: dataset.id,
                                      ),
                                    );
                                  },
                                ).then((v) {
                                  ref
                                      .read(
                                        datasetFileListNotifierProvider
                                            .notifier,
                                      )
                                      .refresh(dataset);
                                });
                              },
                              child: Container(
                                decoration: BoxDecoration(
                                  color: Colors.green,
                                  borderRadius: BorderRadius.circular(20),
                                ),
                                padding: EdgeInsets.all(1),
                                child: Icon(
                                  Icons.add,
                                  color: Colors.white,
                                  size: 18,
                                ),
                              ),
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                  Expanded(
                    child: Text.rich(
                      TextSpan(
                        children: [
                          TextSpan(
                            text: "${t.dataset_screen.table.status}: ",
                            style: TextStyle(
                              fontWeight: FontWeight.bold,
                              fontSize: 12,
                            ),
                          ),
                          TextSpan(
                            text: getStatus(data.status),
                            style: TextStyle(fontSize: 12),
                          ),
                        ],
                      ),
                    ),
                  ),
                ],
              ),
              Divider(),
              if (data.sampleFile != null)
                Text.rich(
                  TextSpan(
                    children: [
                      TextSpan(
                        text: "${t.dataset_screen.table.preview}: ",
                        style: TextStyle(
                          fontWeight: FontWeight.bold,
                          fontSize: 12,
                        ),
                      ),
                      TextSpan(
                        text: data.sampleFile,
                        style: TextStyle(fontSize: 12),
                      ),
                    ],
                  ),
                ),
              Expanded(
                child: Container(
                  decoration: BoxDecoration(
                    borderRadius: BorderRadius.circular(4),
                  ),
                  child: _ListFile(state: data),
                ),
              ),
            ],
          ),
        );
      },
      error: (Object error, StackTrace stackTrace) {
        return Center(child: Text(error.toString()));
      },
      loading: () {
        return Center(child: CircularProgressIndicator());
      },
    );
  }
}

class _ListFile extends ConsumerWidget {
  const _ListFile({required this.state});
  final DatasetFileState state;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return SizedBox(
      child:
          state.currentContent != null && state.currentContent!.isNotEmpty
              ? Image.network(state.currentContent!)
              : Center(
                child: Text(
                  t.dataset_screen.table.no_preview,
                  style: Styles.defaultButtonTextStyle,
                ),
              ),
    );
  }
}
