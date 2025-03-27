import 'dart:ui' as ui;

import 'package:auto_ml/modules/label/components/annotation_widget.dart';
import 'package:auto_ml/modules/label/notifiers/image_notifier.dart';
import 'package:auto_ml/modules/label/notifiers/label_notifier.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class ImageBoard extends ConsumerStatefulWidget {
  const ImageBoard({super.key, required this.dl, required this.current});
  final (String, String) dl;
  final String current;

  @override
  ConsumerState<ImageBoard> createState() => _ImageBoardState();
}

class _ImageBoardState extends ConsumerState<ImageBoard> {
  final TransformationController _transformationController =
      TransformationController();

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(imageNotifierProvider(widget.current));
    final annotations =
        ref.read(labelNotifierProvider(widget.dl)).currentLabels;

    return state.when(
      data: (data) {
        if (data.current.isEmpty) {
          return Center(child: Text("No data"));
        }

        return Center(
          child: InteractiveViewer(
            transformationController: _transformationController,
            boundaryMargin: EdgeInsets.all(0),
            minScale: 0.5,
            maxScale: 2.0,
            constrained: false,
            child: SizedBox(
              width: data.size.width,
              height: data.size.height,
              child: CustomPaint(
                size: data.size,
                painter: _ImagePainter(
                  data.image!,
                  _transformationController.value,
                ),
                child: Stack(
                  children:
                      annotations
                          .map(
                            (e) => AnnotationWidget(
                              transform: _transformationController.value,
                              annotation: e,
                              onPanUpdate: (details) {
                                ref
                                    .read(
                                      labelNotifierProvider(widget.dl).notifier,
                                    )
                                    .updateAnnotation(e, dragDetails: details);
                              },
                              onSizeChanged: (changedValue) {
                                ref
                                    .read(
                                      labelNotifierProvider(widget.dl).notifier,
                                    )
                                    .updateAnnotation(
                                      e,
                                      sizeChanged: changedValue,
                                    );
                              },
                            ),
                          )
                          .toList(),
                ),
              ),
            ),
          ),
        );
      },
      error: (error, stackTrace) => Center(child: Text(error.toString())),
      loading: () => Center(child: CircularProgressIndicator()),
    );
  }
}

class _ImagePainter extends CustomPainter {
  final ui.Image image;
  final Matrix4 transform;

  _ImagePainter(this.image, this.transform);

  @override
  void paint(Canvas canvas, Size size) {
    canvas.drawImage(image, Offset.zero, Paint());
  }

  @override
  bool shouldRepaint(covariant _ImagePainter oldDelegate) {
    return oldDelegate.transform != transform;
  }
}
