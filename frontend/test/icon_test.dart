import 'package:flutter/material.dart';

class VSCodeLikeIcon extends StatelessWidget {
  final double size;
  final bool isSelected;

  const VSCodeLikeIcon({super.key, this.size = 100.0, this.isSelected = false});

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: size,
      height: size,
      child: CustomPaint(painter: _VSCodeLikePainter(isSelected)),
    );
  }
}

class _VSCodeLikePainter extends CustomPainter {
  final bool isSelected;

  _VSCodeLikePainter(this.isSelected);

  @override
  void paint(Canvas canvas, Size size) {
    final borderPaint =
        Paint()
          ..color = isSelected ? Colors.white : Colors.black
          ..style = PaintingStyle.stroke
          ..strokeWidth = 1.0;

    final double rectWidth = size.width / 5;
    final double middleWidth = rectWidth * 3; // 中间矩形宽度
    final double gap = 0; // 计算缝隙宽度

    // 左边矩形
    Rect leftRect = Rect.fromLTWH(0, 0, rectWidth, size.height);
    canvas.drawRect(leftRect, borderPaint);

    // 右边矩形
    Rect rightRect = Rect.fromLTWH(
      size.width - rectWidth,
      0,
      rectWidth,
      size.height,
    );
    canvas.drawRect(rightRect, borderPaint);

    // 中间矩形（带缝隙）
    Rect middleRect = Rect.fromLTWH(
      rectWidth + gap,
      0,
      middleWidth - 2 * gap,
      size.height,
    );
    canvas.drawRect(middleRect, borderPaint);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}

void main() {
  runApp(
    MaterialApp(
      home: Scaffold(
        backgroundColor: Colors.grey[900],
        body: Center(child: VSCodeLikeIcon(size: 30, isSelected: true)),
      ),
    ),
  );
}
