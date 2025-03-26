import 'package:auto_ml/modules/label/models/annotation.dart';
import 'package:flutter/material.dart';

class AnnotationWidget extends StatelessWidget {
  const AnnotationWidget({
    super.key,
    required this.transform,
    required this.annotation,
    required this.onPanUpdate,
  });
  final Matrix4 transform;
  final Annotation annotation;
  final Function(DragUpdateDetails details) onPanUpdate;
  @override
  Widget build(BuildContext context) {
    return Positioned(
      left: annotation.position.dx,
      top: annotation.position.dy,
      child: GestureDetector(
        onPanUpdate: (details) {
          onPanUpdate(details);
        },
        child: Container(
          width: annotation.width,
          height: annotation.height,
          decoration: BoxDecoration(
            color: Colors.red.withValues(alpha: 0.5),
            border: Border.all(),
          ),
          child: Center(
            child: Text("${annotation.position.dx}, ${annotation.position.dy}"),
          ),
        ),
      ),
    );
  }
}
