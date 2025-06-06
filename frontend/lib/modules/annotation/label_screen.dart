import 'package:auto_ml/i18n/strings.g.dart';
import 'package:auto_ml/modules/annotation/components/annotation_list_widget.dart';
import 'package:auto_ml/modules/annotation/components/cls_annotation_widget.dart';
import 'package:auto_ml/modules/annotation/components/mllm_annotation_widget.dart';
import 'package:auto_ml/modules/annotation/components/select_dataset_annotations_dialog.dart';
import 'package:auto_ml/modules/current_dataset_annotation_notifier.dart';
import 'package:auto_ml/modules/annotation/components/file_list.dart';
import 'package:auto_ml/modules/annotation/components/icons.dart';
import 'package:auto_ml/modules/annotation/components/image_board.dart';
import 'package:auto_ml/utils/logger.dart';
import 'package:auto_ml/utils/styles.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class LabelScreen extends ConsumerStatefulWidget {
  const LabelScreen({super.key});

  @override
  ConsumerState<LabelScreen> createState() => _LabelScreenState();
}

class _LabelScreenState extends ConsumerState<LabelScreen> {
  late final Widget _cachedDropDownButton;

  @override
  void initState() {
    super.initState();
    _cachedDropDownButton = LayoutIcons(onIconSelected: (_) {});
  }

  @override
  Widget build(BuildContext context) {
    final current = ref.watch(currentDatasetAnnotationNotifierProvider);
    logger.d(
      "Current dataset: ${current.dataset?.id}, Current annotation: ${current.annotation?.id} , files: ${current.data.length}",
    );

    if (current.annotation == null ||
        current.dataset == null ||
        current.dataset?.id == 0 ||
        current.annotation?.id == null) {
      return Center(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.center,
          mainAxisAlignment: MainAxisAlignment.center,
          spacing: 10,
          children: [
            Text(t.label_screen.not_selected),
            TextButton(
              onPressed: () {
                showGeneralDialog(
                  barrierColor: Styles.barriarColor,
                  barrierDismissible: true,
                  barrierLabel: "not selected",
                  context: context,
                  pageBuilder: (c, _, __) {
                    return Center(child: SelectDatasetAnnotationsDialog());
                  },
                );
              },
              child: Text(
                t.label_screen.select,
                style: Styles.defaultButtonTextStyle,
              ),
            ),
          ],
        ),
      );
    }

    if (current.annotation!.annotationType == 3) {
      return MllmAnnotationWidget(data: current.data);
    } else if (current.annotation!.annotationType == 1) {
      return Container(
        padding: EdgeInsets.only(top: 10, bottom: 10),
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(10),

          gradient: LinearGradient(
            begin: Alignment.centerLeft,
            end: Alignment.centerRight,
            stops: [0.1, 0.9, 1.0],
            colors: [Colors.grey[200]!, Colors.white, Colors.grey[200]!],
          ),
        ),
        child: Column(
          spacing: 10,
          children: [
            SizedBox(height: 20, child: _cachedDropDownButton),
            Expanded(
              child: Row(
                spacing: 10,
                children: [
                  FileList(data: current.data),
                  Expanded(child: ImageBoard()),
                  AnnotationListWidget(
                    classes:
                        ref
                            .read(currentDatasetAnnotationNotifierProvider)
                            .classes,
                  ),
                ],
              ),
            ),
          ],
        ),
      );
    } else if (current.annotation!.annotationType == 0) {
      return ClsAnnotationWidget(data: current.data);
    }
    return Center(
      child: Text("Unsupport type", style: Styles.defaultButtonTextStyle),
    );
  }
}
