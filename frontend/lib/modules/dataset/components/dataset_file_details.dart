import 'package:auto_ml/i18n/strings.g.dart';
import 'package:auto_ml/modules/dataset/notifier/dataset_file_list_notifier.dart';
import 'package:auto_ml/modules/dataset/notifier/dataset_file_state.dart';
import 'package:auto_ml/modules/dataset/notifier/dataset_notifier.dart';
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
        return "Unknown";
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
                    child: Text.rich(
                      TextSpan(
                        children: [
                          TextSpan(
                            text: "Current count: ",
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
                  ),
                  Expanded(
                    child: Text.rich(
                      TextSpan(
                        children: [
                          TextSpan(
                            text: "Status: ",
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
                        text: "Preview: ",
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
          state.currentContent != null
              ? Image.network(state.currentContent!)
              : null,
    );
  }
}
