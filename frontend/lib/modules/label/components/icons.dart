import 'package:flutter/material.dart';

class TopToBottomIconPainter extends CustomPainter {
  final bool isSelected;

  TopToBottomIconPainter(this.isSelected);

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

class LeftToRightIconPainter extends CustomPainter {
  final bool isSelected;

  LeftToRightIconPainter(this.isSelected);

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

class LayoutIcons extends StatelessWidget {
  const LayoutIcons({super.key, required this.onIconSelected});
  final Function(int type) onIconSelected;

  @override
  Widget build(BuildContext context) {
    return Row(
      spacing: 10,
      crossAxisAlignment: CrossAxisAlignment.end,

      children: [
        Spacer(),
        InkWell(
          onTap: () {
            onIconSelected(0);
          },
          child: SizedBox(
            width: 15,
            height: 15,
            child: CustomPaint(painter: LeftToRightIconPainter(false)),
          ),
        ),
        InkWell(
          onTap: () {
            onIconSelected(1);
          },
          child: SizedBox(
            width: 15,
            height: 15,
            child: CustomPaint(painter: TopToBottomIconPainter(false)),
          ),
        ),
        SizedBox(width: 1),
      ],
    );
  }
}
