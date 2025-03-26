import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'dart:ui' as ui;

void main() {
  runApp(MaterialApp(home: ImageAnnotationScreen()));
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
          boundaryMargin: EdgeInsets.all(0), // 允许拖拽到图片边界
          minScale: 0.5,
          maxScale: 5.0,
          constrained: false,
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
