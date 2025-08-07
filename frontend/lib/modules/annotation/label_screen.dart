import 'package:auto_ml/i18n/strings.g.dart';
import 'package:auto_ml/modules/annotation/components/annotation_list_widget.dart';
import 'package:auto_ml/modules/annotation/components/cls_annotation_widget.dart';
import 'package:auto_ml/modules/annotation/components/mllm_annotation_widget.dart';
import 'package:auto_ml/modules/annotation/components/select_dataset_annotations_dialog.dart';
import 'package:auto_ml/modules/current_dataset_annotation_notifier.dart';
import 'package:auto_ml/modules/annotation/components/file_list.dart';
import 'package:auto_ml/modules/annotation/components/icons.dart';
import 'package:auto_ml/modules/annotation/components/image_board.dart';
import 'package:auto_ml/utils/globals.dart';
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
    final (annotation, dataset) = ref.watch(
      currentDatasetAnnotationNotifierProvider.select(
        (state) => (state.annotation, state.dataset),
      ),
    );

    // You can still log, but get the other values with `read` inside the log.
    // This avoids creating a dependency.
    logger.d(
      "Router rebuilding. Annotation ID: ${annotation?.id}, Type: ${annotation?.annotationType}",
    );

    if (annotation == null || dataset == null || dataset.id == 0) {
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
                  pageBuilder: (c, _, _) {
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

    if (annotation.annotationType == 3) {
      return Padding(
        padding: EdgeInsetsGeometry.all(10),
        child: Column(
          spacing: 10,
          children: [
            SizedBox(height: 20, child: _cachedDropDownButton),
            Expanded(child: MllmAnnotationWidget()),
          ],
        ),
      );
    } else if (annotation.annotationType == 1) {
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
              child: Padding(
                padding: EdgeInsetsGeometry.only(left: 10, right: 10),
                child: Row(
                  spacing: 10,
                  children: [
                    FileList(),
                    Expanded(
                      child: ImageBoard(key: Globals.globalImageBoardKey),
                    ),
                    AnnotationListWidget(
                      classes:
                          ref
                              .read(currentDatasetAnnotationNotifierProvider)
                              .classes,
                    ),
                  ],
                ),
              ),
            ),
            SizedBox(
              height: 40,
              child: Row(
                mainAxisAlignment: MainAxisAlignment.center,
                spacing: 30,
                children: [
                  ElevatedButton(
                    style: Styles.getDefaultButtonStyle(
                      width: 150,
                      height: 40,
                      radius: 20,
                      backgroundColor: Theme.of(
                        context,
                      ).primaryColor.withAlpha(200),
                    ),
                    onPressed: () {
                      ref
                          .read(
                            currentDatasetAnnotationNotifierProvider.notifier,
                          )
                          .prevData();
                    },
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.center,
                      mainAxisAlignment: MainAxisAlignment.center,
                      spacing: 10,
                      children: [
                        Icon(Icons.arrow_back, size: 16, color: Colors.white),
                        Text(
                          t.annotation_screen.list.prev,
                          style: Styles.defaultButtonTextStyle.copyWith(
                            color: Colors.white,
                          ),
                        ),
                      ],
                    ),
                  ),
                  ElevatedButton(
                    style: Styles.getDefaultButtonStyle(
                      width: 150,
                      height: 40,
                      radius: 20,
                      backgroundColor: Theme.of(
                        context,
                      ).primaryColor.withAlpha(200),
                    ),
                    onPressed: () {
                      ref
                          .read(
                            currentDatasetAnnotationNotifierProvider.notifier,
                          )
                          .nextData();
                    },
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.center,
                      mainAxisAlignment: MainAxisAlignment.center,
                      spacing: 10,
                      children: [
                        Text(
                          t.annotation_screen.list.next,
                          style: Styles.defaultButtonTextStyle.copyWith(
                            color: Colors.white,
                          ),
                        ),
                        Icon(
                          Icons.arrow_forward,
                          size: 16,
                          color: Colors.white,
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      );
    } else if (annotation.annotationType == 0) {
      // return ClsAnnotationWidget(data: current.data);
      return Padding(
        padding: EdgeInsetsGeometry.all(10),
        child: Column(
          spacing: 10,
          children: [
            SizedBox(height: 20, child: _cachedDropDownButton),
            Expanded(child: ClsAnnotationWidget()),
          ],
        ),
      );
    }
    return Center(
      child: Text("Unsupport type", style: Styles.defaultButtonTextStyle),
    );
  }
}
