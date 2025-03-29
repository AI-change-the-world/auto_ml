import 'package:auto_ml/modules/label/models/polygon_annotation.dart';
import 'package:flutter/material.dart';

class PolygonAnnotationWidget extends StatelessWidget {
  const PolygonAnnotationWidget({
    super.key,
    required this.annotation,
    @Deprecated("why polygon needs to change position?") this.onPanUpdate,
    required this.onVertexDrag,
  });

  final PolygonAnnotation annotation;
  final Function(DragUpdateDetails details)? onPanUpdate;
  final Function(int index, DragUpdateDetails details) onVertexDrag;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      // onPanUpdate: onPanUpdate,
      child: CustomPaint(
        painter: PolygonPainter(annotation),
        child: Stack(
          children: _buildVertexHandles(), // 画点的拖拽手柄
        ),
      ),
    );
  }

  /// 创建可拖拽的多边形顶点
  List<Widget> _buildVertexHandles() {
    return List.generate(annotation.points.length, (index) {
      Offset point = annotation.points[index];
      return Positioned(
        left: point.dx - 8,
        top: point.dy - 8,
        child: GestureDetector(
          onPanUpdate: (details) {
            onVertexDrag(index, details);
          },
          child: Container(
            width: 16,
            height: 16,
            decoration: BoxDecoration(
              color: Colors.blue,
              shape: BoxShape.circle,
            ),
          ),
        ),
      );
    });
  }
}

class PolygonPainter extends CustomPainter {
  final PolygonAnnotation annotation;

  PolygonPainter(this.annotation);

  @override
  void paint(Canvas canvas, Size size) {
    Paint paint =
        Paint()
          ..color =
              annotation.selected
                  ? Colors.red.withValues(alpha: .5)
                  : Colors.red.withValues(alpha: .3)
          ..style = PaintingStyle.fill;

    Paint borderPaint =
        Paint()
          ..color = annotation.editable ? Colors.red : Colors.grey
          ..strokeWidth = 2
          ..style = PaintingStyle.stroke;

    Path path = Path()..addPolygon(annotation.points, true);

    canvas.drawPath(path, paint);
    canvas.drawPath(path, borderPaint);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) {
    return true;
  }
}
