// ignore_for_file: library_private_types_in_public_api

import 'package:auto_ml/modules/label/components/polygon_annotation_widget.dart';
import 'package:auto_ml/modules/label/models/polygon_annotation.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'dart:ui' as ui;

void main() {
  runApp(MaterialApp(home: ImageAnnotationScreen()));
}

class ImageAnnotationPainter extends CustomPainter {
  final ui.Image image;

  ImageAnnotationPainter(this.image);

  @override
  void paint(Canvas canvas, Size size) {
    canvas.save();
    canvas.drawImage(image, Offset.zero, Paint());

    canvas.restore();
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) {
    return true;
  }
}

class ImageAnnotationScreen extends StatefulWidget {
  const ImageAnnotationScreen({super.key});

  @override
  _ImageAnnotationScreenState createState() => _ImageAnnotationScreenState();
}

class _ImageAnnotationScreenState extends State<ImageAnnotationScreen> {
  late ui.Image _image;
  Size _imageSize = Size.zero;
  final TransformationController _transformationController =
      TransformationController();
  List<PolygonAnnotation> annotations = [];
  int? activeAnnotationIndex;
  int? activeVertexIndex;
  int? activeEdgeIndex;

  @override
  void initState() {
    super.initState();
    _loadImage();
    annotations = [
      PolygonAnnotation([
        Offset(300, 200),
        Offset(400, 500),
        Offset(500, 600),
      ], 1),
      PolygonAnnotation([
        Offset(600, 500),
        Offset(700, 600),
        Offset(800, 700),
      ], 2),
    ];
  }

  @override
  void dispose() {
    _transformationController.dispose();
    super.dispose();
  }

  void _loadImage() async {
    final ByteData data = await rootBundle.load('assets/test.png');
    final List<int> bytes = data.buffer.asUint8List();
    final ui.Image image = await decodeImageFromList(Uint8List.fromList(bytes));
    setState(() {
      _image = image;
      _imageSize = Size(image.width.toDouble(), image.height.toDouble());
    });
  }

  double _distanceToSegment(Offset p, Offset v, Offset w) {
    final double l2 = (w - v).distanceSquared;
    if (l2 == 0.0) return (p - v).distance;
    final double t = ((p - v).dx * (w - v).dx + (p - v).dy * (w - v).dy) / l2;
    final double tClamped = t.clamp(0.0, 1.0);
    final Offset projection = v + (w - v) * tClamped;
    return (p - projection).distance;
  }

  void _onPanStart(DragStartDetails details) {
    final localPosition = details.localPosition;

    for (int i = 0; i < annotations.length; i++) {
      final annotation = annotations[i];

      // 检查顶点
      final vertexIndex = _getClosestVertexIndex(annotation, localPosition);
      if (vertexIndex != null) {
        setState(() {
          activeAnnotationIndex = i;
          activeVertexIndex = vertexIndex;
          activeEdgeIndex = null;
        });
        return;
      }

      // 检查边
      final edgeIndex = _getClosestEdgeIndex(annotation, localPosition);
      if (edgeIndex != null) {
        _handleEdgeInsertion(i, edgeIndex);
        return;
      }
    }
  }

  int? _getClosestVertexIndex(PolygonAnnotation annotation, Offset point) {
    for (int i = 0; i < annotation.points.length; i++) {
      if ((annotation.points[i] - point).distance < 10) {
        return i;
      }
    }
    return null;
  }

  int? _getClosestEdgeIndex(PolygonAnnotation annotation, Offset point) {
    final points = annotation.points;
    for (int i = 0; i < points.length; i++) {
      final v = points[i];
      final w = points[(i + 1) % points.length];
      if (_distanceToSegment(point, v, w) < 10) {
        return i;
      }
    }
    return null;
  }

  void _handleEdgeInsertion(int annotationIndex, int edgeIndex) {
    final annotation = annotations[annotationIndex];
    final newPoints = List<Offset>.from(annotation.points);
    final newPoint =
        (annotation.points[edgeIndex] +
            annotation.points[(edgeIndex + 1) % annotation.points.length]) /
        2;
    newPoints.insert(edgeIndex + 1, newPoint);

    setState(() {
      annotations[annotationIndex] = annotation.copyWith(points: newPoints);
      activeAnnotationIndex = annotationIndex;
      activeVertexIndex = edgeIndex + 1;
      activeEdgeIndex = null;
    });
  }

  void _onPanUpdate(DragUpdateDetails details) {
    if (activeAnnotationIndex == null || activeVertexIndex == null) return;

    setState(() {
      final annotation = annotations[activeAnnotationIndex!];
      final newPoints = List<Offset>.from(annotation.points);
      newPoints[activeVertexIndex!] += details.delta;
      annotations[activeAnnotationIndex!] = annotation.copyWith(
        points: newPoints,
      );
    });
  }

  void _onPanEnd(DragEndDetails details) {
    setState(() {
      activeAnnotationIndex = null;
      activeVertexIndex = null;
      activeEdgeIndex = null;
    });
  }

  @override
  Widget build(BuildContext context) {
    if (_imageSize.width == 0 || _imageSize.height == 0) {
      return Scaffold(
        appBar: AppBar(title: Text('Image Annotation')),
        body: Center(child: CircularProgressIndicator()),
      );
    }

    return Scaffold(
      appBar: AppBar(title: Text('Image Annotation')),
      body: Center(
        child: InteractiveViewer(
          transformationController: _transformationController,
          boundaryMargin: EdgeInsets.all(0),
          minScale: 0.5,
          maxScale: 5.0,
          constrained: false,
          child: SizedBox(
            width: _imageSize.width,
            height: _imageSize.height,
            child: CustomPaint(
              size: _imageSize,
              painter: ImageAnnotationPainter(_image),
              child: GestureDetector(
                onTapDown: (details) {
                  final localPosition = details.localPosition;
                  final annotation =
                      annotations
                          .where((t) => t.isPointInPolygon(localPosition))
                          .firstOrNull;
                  if (annotation == null) {
                    setState(() {
                      for (final i in annotations) {
                        i.selected = false;
                      }
                    });
                  } else {
                    setState(() {
                      // annotation.selected = true;
                      for (final i in annotations) {
                        i.selected = i == annotation;
                      }
                    });
                  }
                },
                behavior: HitTestBehavior.translucent,
                onPanStart: _onPanStart,
                onPanUpdate: _onPanUpdate,
                onPanEnd: _onPanEnd,
                child: Stack(
                  children:
                      annotations
                          .map(
                            (e) => PolygonAnnotationWidget(
                              annotation: e,

                              onVertexDrag: (
                                int index,
                                DragUpdateDetails details,
                              ) {
                                setState(() {
                                  e.points[index] += details.delta;
                                });
                              },
                            ),
                          )
                          .toList(),
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
