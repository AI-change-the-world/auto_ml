// this widget is used to test

import 'package:auto_ml/modules/label/components/file_list.dart';
import 'package:auto_ml/modules/label/components/icons.dart';
import 'package:auto_ml/modules/label/components/image_board.dart';
import 'package:auto_ml/modules/label/notifiers/annotation_notifier.dart';
import 'package:auto_ml/utils/logger.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class TestLabelScreen extends ConsumerStatefulWidget {
  const TestLabelScreen({super.key, this.assetImg = "", this.assetLabel = ""});
  final String assetImg;
  final String assetLabel;

  @override
  ConsumerState<TestLabelScreen> createState() => _TestLabelScreenState();
}

class _TestLabelScreenState extends ConsumerState<TestLabelScreen> {
  late String dataPath = widget.assetImg;
  late String labelPath = widget.assetLabel;

  @override
  void initState() {
    super.initState();

    WidgetsBinding.instance.addPostFrameCallback((_) {
      Future.microtask(() {
        ref
            .read(annotationNotifierProvider.notifier)
            .setAnnotations(dataPath, labelPath, 1, 1);
      });
    });
  }

  @override
  Widget build(BuildContext context) {
    logger.d("dataPath: $dataPath, labelPath: $labelPath");

    return Column(
      spacing: 10,
      children: [
        SizedBox(height: 20, child: LayoutIcons(onIconSelected: (type) {})),
        Expanded(
          child: Row(
            spacing: 10,
            children: [
              FileList(
                current: dataPath,
                data: [MapEntry(dataPath, labelPath)],
                dl: (dataPath, labelPath),
              ),
              Expanded(child: ImageBoard(current: dataPath)),
            ],
          ),
        ),
      ],
    );
  }
}
