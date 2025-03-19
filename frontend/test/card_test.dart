import 'package:auto_ml/utils/logger.dart';
import 'package:flutter/material.dart';

void main() {
  runApp(
    const MaterialApp(home: Scaffold(body: Center(child: InteractiveCard()))),
  );
}

class InteractiveCard extends StatefulWidget {
  const InteractiveCard({super.key});

  @override
  State<InteractiveCard> createState() => _InteractiveCardState();
}

class _InteractiveCardState extends State<InteractiveCard> {
  double _xRotation = 0;
  double _yRotation = 0;
  final double maxAngle = 0.3; // 最大旋转角度（弧度）

  // void _updateRotation(Offset position, Size size) {
  //   double dx = (position.dx / size.width - 0.5) * 2; // -1 ~ 1
  //   double dy = (position.dy / size.height - 0.5) * 2; // -1 ~ 1

  //   double newXRotation = dy * 0.3;
  //   double newYRotation = dx * -0.3;

  //   logger.d('newXRotation: $newXRotation, newYRotation: $newYRotation');

  //   // 只有在值变化时才调用 setState
  //   if ((newXRotation - _xRotation).abs() > 0.01 ||
  //       (newYRotation - _yRotation).abs() > 0.01) {
  //     setState(() {
  //       _xRotation = newXRotation;
  //       _yRotation = newYRotation;
  //     });
  //   }
  // }

  void _updateRotation(Offset position, Size size) {
    double dx = (position.dx - size.width / 2) / (size.width / 2); // -1 ~ 1
    double dy = (position.dy - size.height / 2) / (size.height / 2); // -1 ~ 1

    // 计算旋转角度，映射到 [-maxAngle, maxAngle]
    double newXRotation = dy * -maxAngle;
    double newYRotation = dx * maxAngle;
    logger.d('newXRotation: $newXRotation, newYRotation: $newYRotation');
    // 只有角度变化超过一定阈值才更新，防止 setState 过于频繁
    if ((newXRotation - _xRotation).abs() > 0.01 ||
        (newYRotation - _yRotation).abs() > 0.01) {
      setState(() {
        _xRotation = newXRotation;
        _yRotation = newYRotation;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return MouseRegion(
      onHover: (event) {
        final RenderBox box = context.findRenderObject() as RenderBox;
        final Offset localPosition = box.globalToLocal(event.position);
        _updateRotation(localPosition, box.size);
      },
      onExit: (_) {
        logger.d('onExit');
        setState(() {
          _xRotation = 0;
          _yRotation = 0;
        });
      },
      child: Transform(
        // duration: const Duration(milliseconds: 100),
        transform:
            Matrix4.identity()
              ..setEntry(3, 2, 0.0015) // 透视效果
              ..rotateX(_xRotation)
              ..rotateY(_yRotation),
        child: Container(
          width: 200,
          height: 200,
          decoration: BoxDecoration(
            color: Colors.blue,
            borderRadius: BorderRadius.circular(20),
            boxShadow: [
              BoxShadow(
                color: Colors.black.withValues(alpha: 0.2),
                blurRadius: 10,
                spreadRadius: 2,
                offset: Offset(-_yRotation * 20, _xRotation * 20),
              ),
            ],
          ),
          alignment: Alignment.center,
          child: const Text(
            "Hover Me",
            style: TextStyle(fontSize: 20, color: Colors.white),
          ),
        ),
      ),
    );
  }
}
