import 'package:auto_ml/utils/logger.dart';
import 'package:auto_ml/utils/toast_utils.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'dart:ui' as ui;

void main() {
  runApp(
    MaterialApp(
      debugShowCheckedModeBanner: false,
      home: ImageAnnotationScreen(),
    ),
  );
}

class ImageAnnotationScreen extends StatefulWidget {
  const ImageAnnotationScreen({super.key});

  @override
  // ignore: library_private_types_in_public_api
  _ImageAnnotationScreenState createState() => _ImageAnnotationScreenState();
}

class _ImageAnnotationScreenState extends State<ImageAnnotationScreen> {
  final List<Annotation> annotations = [
    Annotation(Offset(100, 150), 100, 50),
    Annotation(Offset(250, 350), 120, 60),
  ];

  late ui.Image _image;
  Size _imageSize = Size.zero;
  final TransformationController _transformationController =
      TransformationController();

  @override
  void initState() {
    super.initState();
    _loadImage();
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

  Offset? startPoint;
  Rect? previewRect;

  bool enable = false;
  FocusNode focusNode = FocusNode();

  getImagePosition(DragStartDetails details) {
    // 使用 Matrix4 的逆变换，把当前屏幕坐标转成图像坐标
    final matrix = _transformationController.value;
    final inverseMatrix = Matrix4.inverted(matrix);
    final imagePosition = MatrixUtils.transformPoint(
      inverseMatrix,
      details.localPosition,
    );
    return imagePosition;
  }

  @override
  Widget build(BuildContext context) {
    if (_imageSize.width == 0 || _imageSize.height == 0) {
      return Scaffold(
        appBar: AppBar(title: Text('Image Annotation')),
        body: Center(child: CircularProgressIndicator()),
      );
    }

    return KeyboardListener(
      onKeyEvent: (value) {
        if (value.logicalKey == LogicalKeyboardKey.keyW &&
            value is KeyDownEvent) {
          setState(() {
            enable = !enable;
          });
          ToastUtils.info(context, title: enable ? '开启' : '关闭');
        }
      },
      focusNode: focusNode,
      child: Scaffold(
        appBar: AppBar(
          title: Text('Image Annotation'),
          actions: [
            InkWell(
              onTap: () {
                setState(() {
                  enable = !enable;
                });
              },
              child: Icon(Icons.phone_enabled),
            ),
          ],
        ),
        body: Center(
          child: InteractiveViewer(
            panEnabled: enable,
            scaleEnabled: enable,
            transformationController: _transformationController,
            boundaryMargin: EdgeInsets.all(0), // 允许拖拽到图片边界
            minScale: 0.5,
            maxScale: 2.0,
            constrained: false,
            child: GestureDetector(
              onTap: () {
                focusNode.requestFocus();
              },
              onPanStart: (details) {
                if (enable) {
                  return;
                }
                final imagePosition = getImagePosition(details);
                startPoint = imagePosition;
                logger.i("startPoint: ${details.localPosition}");
                previewRect = Rect.zero;
                annotations.add(Annotation(details.localPosition, 0, 0));
                setState(() {});
              },
              onPanUpdate: (details) {
                if (enable) {
                  return;
                }

                // final currentPoint = details.localPosition;
                // previewRect = Rect.fromPoints(startPoint!, currentPoint);
                final currentPoint = MatrixUtils.transformPoint(
                  Matrix4.inverted(_transformationController.value),
                  details.localPosition,
                );
                previewRect = Rect.fromPoints(startPoint!, currentPoint);
                annotations.removeLast();
                annotations.add(
                  Annotation(
                    Offset(previewRect!.left, previewRect!.top),
                    previewRect!.width,
                    previewRect!.height,
                  ),
                );
                setState(() {});
              },
              onPanEnd: (details) {
                if (enable) {
                  return;
                }
                final rect = previewRect!;
                final annotation = Annotation(
                  Offset(rect.left, rect.top),
                  rect.width,
                  rect.height,
                );
                annotations.removeLast();
                annotations.add(annotation);

                startPoint = null;
                previewRect = null;
                setState(() {});
              },
              child: SizedBox(
                width: _imageSize.width,
                height: _imageSize.height,
                child: CustomPaint(
                  size: _imageSize, // 确保CustomPaint有正确尺寸
                  painter: ImageAnnotationPainter(
                    _image,
                    annotations,
                    _transformationController.value,
                  ),
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class Annotation {
  Offset position;
  double width;
  double height;

  Annotation(this.position, this.width, this.height);
}

// class ImageAnnotationPainter extends CustomPainter {
//   final ui.Image image;
//   final List<Annotation> annotations;
//   final Matrix4 transform;

//   ImageAnnotationPainter(this.image, this.annotations, this.transform);

//   @override
//   void paint(Canvas canvas, Size size) {
//     Paint paint =
//         Paint()
//           // ignore: deprecated_member_use
//           ..color = Colors.red.withOpacity(0.7)
//           ..style = PaintingStyle.stroke
//           ..strokeWidth = 2;

//     canvas.save();
//     // canvas.transform(transform.storage);
//     Matrix4 inverseTransform = Matrix4.inverted(transform);
//     canvas.transform(inverseTransform.storage);
//     canvas.drawImage(image, Offset.zero, Paint());

//     for (var annotation in annotations) {
//       canvas.drawRect(
//         Rect.fromLTWH(
//           annotation.position.dx,
//           annotation.position.dy,
//           annotation.width,
//           annotation.height,
//         ),
//         paint,
//       );
//     }

//     canvas.restore();
//   }

//   @override
//   bool shouldRepaint(covariant CustomPainter oldDelegate) {
//     return true;
//   }
// }

class ImageAnnotationPainter extends CustomPainter {
  final ui.Image image;
  final List<Annotation> annotations;
  final Matrix4 transform;

  ImageAnnotationPainter(this.image, this.annotations, this.transform);

  @override
  void paint(Canvas canvas, Size size) {
    Paint paint =
        Paint()
          // ignore: deprecated_member_use
          ..color = Colors.red.withOpacity(0.7)
          ..style = PaintingStyle.stroke
          ..strokeWidth = 2;

    // 获取转换矩阵的缩放和偏移
    final double scaleX = transform.getMaxScaleOnAxis();
    final double scaleY = scaleX; // 假设等比例缩放
    final Offset translation = Offset(transform[12], transform[13]); // 提取偏移量

    canvas.save();
    canvas.drawImage(image, Offset.zero, Paint());

    for (var annotation in annotations) {
      // 计算变换后的坐标
      final double x = annotation.position.dx * scaleX + translation.dx;
      final double y = annotation.position.dy * scaleY + translation.dy;
      final double w = annotation.width * scaleX;
      final double h = annotation.height * scaleY;

      canvas.drawRect(Rect.fromLTWH(x, y, w, h), paint);
    }

    canvas.restore();
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) {
    return true;
  }
}
