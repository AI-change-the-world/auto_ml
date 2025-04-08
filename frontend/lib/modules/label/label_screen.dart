import 'package:auto_ml/modules/label/components/file_list.dart';
import 'package:auto_ml/modules/label/components/icons.dart';
import 'package:auto_ml/modules/label/components/image_board.dart';
import 'package:auto_ml/modules/label/notifiers/label_notifier.dart';
import 'package:file_selector/file_selector.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class LabelScreen extends ConsumerStatefulWidget {
  const LabelScreen({super.key, this.dataPath = "", this.labelPath = ""});
  final String dataPath;
  final String labelPath;

  @override
  ConsumerState<LabelScreen> createState() => _LabelScreenState();
}

class _LabelScreenState extends ConsumerState<LabelScreen> {
  late String dataPath = widget.dataPath;
  late String labelPath = widget.labelPath;

  @override
  void initState() {
    super.initState();
  }

  Future pickDataset() async {
    if (dataPath.isEmpty) {
      String? directoryPath = await getDirectoryPath(
        confirmButtonText: "Select Dataset",
      );
      if (directoryPath == null) {
        return;
      }
      dataPath = directoryPath;
    }

    if (labelPath.isEmpty) {
      String? directoryPath = await getDirectoryPath(
        confirmButtonText: "Select Label",
      );
      if (directoryPath == null) {
        return;
      }
      labelPath = directoryPath;
    }

    final _ = ref.read(labelNotifierProvider((dataPath, labelPath)));
  }

  @override
  Widget build(BuildContext context) {
    if (dataPath.isEmpty || labelPath.isEmpty) {
      return Center(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.center,
          mainAxisAlignment: MainAxisAlignment.center,
          spacing: 10,
          children: [
            Text("Dataset or label is not selected"),
            TextButton(
              onPressed: () {
                dataPath = "";
                labelPath = "";
                pickDataset().then((_) {
                  setState(() {});
                });
              },
              child: Text("Select"),
            ),
          ],
        ),
      );
    }

    final state = ref.watch(labelNotifierProvider((dataPath, labelPath)));

    return Column(
      spacing: 10,
      children: [
        SizedBox(height: 20, child: LayoutIcons(onIconSelected: (type) {})),
        Expanded(
          child: Row(
            spacing: 10,
            children: [
              FileList(
                current: state.current,
                data: state.dataLabelPairs,
                dl: (dataPath, labelPath),
              ),
              Expanded(
                child: ImageBoard(
                  dl: (dataPath, labelPath),
                  current: state.current,
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}
