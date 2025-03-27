import 'package:flutter/material.dart';

class VSCodeLikeVerticalIcon extends StatelessWidget {
  final double size;
  final bool isSelected;

  const VSCodeLikeVerticalIcon({
    super.key,
    this.size = 100.0,
    this.isSelected = false,
  });

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: size,
      height: size,
      child: CustomPaint(painter: _VSCodeLikeVerticalPainter(isSelected)),
    );
  }
}

class _VSCodeLikeVerticalPainter extends CustomPainter {
  final bool isSelected;

  _VSCodeLikeVerticalPainter(this.isSelected);

  @override
  void paint(Canvas canvas, Size size) {
    final borderPaint =
        Paint()
          ..color = isSelected ? Colors.white : Colors.black
          ..style = PaintingStyle.stroke
          ..strokeWidth = 1.0;

    final double topHeight = size.height * 0.7;
    final double bottomHeight = size.height * 0.3;
    final double bottomWidth = size.width / 2;

    // 上方矩形
    Rect topRect = Rect.fromLTWH(0, 0, size.width, topHeight);
    canvas.drawRect(topRect, borderPaint);

    // 左下矩形
    Rect bottomLeftRect = Rect.fromLTWH(
      0,
      topHeight,
      bottomWidth,
      bottomHeight,
    );
    canvas.drawRect(bottomLeftRect, borderPaint);

    // 右下矩形
    Rect bottomRightRect = Rect.fromLTWH(
      bottomWidth,
      topHeight,
      bottomWidth,
      bottomHeight,
    );
    canvas.drawRect(bottomRightRect, borderPaint);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}

void main() {
  runApp(
    MaterialApp(
      home: Scaffold(
        backgroundColor: Colors.grey[900],
        body: Center(
          child: VSCodeLikeVerticalIcon(size: 100, isSelected: true),
        ),
      ),
    ),
  );
}
