import 'dart:ui' as ui;

import 'package:auto_ml/i18n/strings.g.dart';
import 'package:auto_ml/modules/annotation/components/annotation_widget.dart';
import 'package:auto_ml/modules/annotation/models/annotation.dart';
import 'package:auto_ml/modules/annotation/notifiers/annotation_notifier.dart';
import 'package:auto_ml/modules/annotation/notifiers/annotation_state.dart';
import 'package:auto_ml/modules/annotation/notifiers/image_notifier.dart';
import 'package:auto_ml/modules/current_dataset_annotation_notifier.dart';
import 'package:auto_ml/utils/logger.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class ImageBoard extends ConsumerStatefulWidget {
  const ImageBoard({super.key});

  @override
  ConsumerState<ImageBoard> createState() => _ImageBoardState();
}

class _ImageBoardState extends ConsumerState<ImageBoard> {
  final TransformationController _transformationController =
      TransformationController();

  FocusNode focusNode = FocusNode();

  @override
  void initState() {
    super.initState();
    focusNode.requestFocus();
  }

  Rect? previewRect;
  Offset? startPoint;

  @override
  void didUpdateWidget(covariant ImageBoard oldWidget) {
    super.didUpdateWidget(oldWidget);
    _transformationController.value = Matrix4.identity();
  }

  @override
  Widget build(BuildContext context) {
    final String current = ref.watch(
      currentDatasetAnnotationNotifierProvider.select((v) => v.currentData),
    );
    if (current.isEmpty) {
      return Center(child: Text(t.annotation_screen.image_board.empty));
    }

    final mode = ref.watch(annotationNotifierProvider.select((v) => v.mode));

    return KeyboardListener(
      onKeyEvent: (value) {
        if (value is KeyDownEvent &&
            value.logicalKey == LogicalKeyboardKey.keyW) {
          ref.read(annotationNotifierProvider.notifier).easyChangeMode();
        }
      },
      focusNode: focusNode,
      child: Center(
        child: Padding(
          padding: const EdgeInsets.only(top: 10, bottom: 10),
          child: InteractiveViewer(
            panEnabled: mode != LabelMode.add,

            ///  scaleEnabled is set to false for better performance
            scaleEnabled: false,
            transformationController: _transformationController,
            boundaryMargin: EdgeInsets.all(0),

            ///  minScale is set to 1 for better performance
            minScale: 1,

            ///  maxScale is set to 1 for better performance
            maxScale: 1,
            constrained: false,
            child: GestureDetector(
              onTap: () {
                focusNode.requestFocus();
                ref
                    .read(annotationNotifierProvider.notifier)
                    .changeCurrentAnnotation("");
              },
              onPanStart: (details) {
                if (mode != LabelMode.add) {
                  return;
                }
                previewRect = null;
                startPoint = null;

                // final imagePosition = getImagePosition(details);
                final imagePosition = details.localPosition;
                previewRect = Rect.zero;
                startPoint = imagePosition;
                logger.d("startPoint: $imagePosition");
                ref
                    .read(annotationNotifierProvider.notifier)
                    .addFakeAnnotation(Annotation(imagePosition, 0, 0, -1));
              },
              onPanUpdate: (details) {
                if (mode != LabelMode.add) {
                  return;
                }
                // final currentPoint = MatrixUtils.transformPoint(
                //   Matrix4.inverted(_transformationController.value),
                //   details.localPosition,
                // );
                previewRect = Rect.fromPoints(
                  startPoint!,
                  details.localPosition,
                );
                ref
                    .read(annotationNotifierProvider.notifier)
                    .addFakeAnnotation(
                      Annotation(
                        startPoint!,
                        previewRect!.width,
                        previewRect!.height,
                        -1,
                      ),
                    );
              },
              onPanEnd: (details) {
                ref
                    .read(annotationNotifierProvider.notifier)
                    .fakeAnnotationFinalize();
                startPoint = null;
                previewRect = null;
              },

              child: Builder(
                builder: (c) {
                  final data = ref.watch(imageNotifierProvider);

                  if (data.image != null) {
                    return SizedBox(
                      width: data.size.width,
                      height: data.size.height,
                      child: CustomPaint(
                        size: data.size,
                        painter: _ImagePainter(data.image!, data.imgKey),
                        child: Builder(
                          builder: (c) {
                            final annotations = ref.watch(
                              annotationNotifierProvider.select(
                                (v) => v.annotations,
                              ),
                            );
                            // logger.d(
                            //   "annotations length: ${annotations.length}",
                            // );
                            return Stack(
                              children:
                                  annotations
                                      .map(
                                        (e) => AnnotationWidget(
                                          classes:
                                              ref
                                                  .read(
                                                    currentDatasetAnnotationNotifierProvider,
                                                  )
                                                  .classes,
                                          transform:
                                              _transformationController.value,
                                          annotation: e,
                                          onPanUpdate: (details) {
                                            ref
                                                .read(
                                                  annotationNotifierProvider
                                                      .notifier,
                                                )
                                                .updateAnnotation(
                                                  e,
                                                  dragDetails: details,
                                                );
                                          },
                                          onSizeChanged: (changedValue) {
                                            ref
                                                .read(
                                                  annotationNotifierProvider
                                                      .notifier,
                                                )
                                                .updateAnnotation(
                                                  e,
                                                  sizeChanged: changedValue,
                                                );
                                          },
                                          onSelected: () {
                                            ref
                                                .read(
                                                  annotationNotifierProvider
                                                      .notifier,
                                                )
                                                .changeCurrentAnnotation(
                                                  e.uuid,
                                                );
                                          },
                                        ),
                                      )
                                      .toList(),
                            );
                          },
                        ),
                      ),
                    );
                  }
                  return Center(child: CircularProgressIndicator());
                },
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class _ImagePainter extends CustomPainter {
  final ui.Image image;
  final String imgName;

  _ImagePainter(this.image, this.imgName);

  @override
  void paint(Canvas canvas, Size size) {
    canvas.drawImage(image, Offset.zero, Paint());
  }

  @override
  bool shouldRepaint(covariant _ImagePainter oldDelegate) {
    bool showRepaint = oldDelegate.imgName != imgName;
    // logger.d("shouldRepaint? $showRepaint");
    return showRepaint;
  }
}
