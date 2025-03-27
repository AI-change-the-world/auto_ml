import 'package:auto_ml/modules/label/models/annotation.dart';
import 'package:auto_ml/modules/label/models/changed.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';

class AnnotationWidget extends StatelessWidget {
  const AnnotationWidget({
    super.key,
    required this.transform,
    required this.annotation,
    required this.onPanUpdate,
    required this.onSizeChanged,
  });
  final Matrix4 transform;
  final Annotation annotation;
  final Function(DragUpdateDetails details) onPanUpdate;
  final Function(List<SizeChanged> changed) onSizeChanged;
  @override
  Widget build(BuildContext context) {
    return Positioned(
      left: annotation.position.dx,
      top: annotation.position.dy,
      child: GestureDetector(
        onPanUpdate: (details) {
          onPanUpdate(details);
        },
        child: Stack(
          children: [
            // 标注框
            MouseRegion(
              cursor: SystemMouseCursors.grab,
              child: Container(
                width: annotation.width,
                height: annotation.height,
                decoration: BoxDecoration(
                  color: Colors.red.withValues(alpha: 0.3),
                  border: Border.all(color: Colors.red, width: 2),
                ),
                child: Center(
                  child: Text(
                    "${annotation.position.dx}, ${annotation.position.dy}",
                    style: TextStyle(fontSize: 12, color: Colors.black),
                  ),
                ),
              ),
            ),
            // 角落 & 边框手柄
            ..._buildResizeHandles(),
          ],
        ),
      ),
    );
  }

  /// 构建 8 个拖拽手柄
  List<Widget> _buildResizeHandles() {
    return [
      _buildHandle(Alignment.topLeft, -1, -1), // 左上角
      _buildHandle(Alignment.topRight, 1, -1), // 右上角
      _buildHandle(Alignment.bottomLeft, -1, 1), // 左下角
      _buildHandle(Alignment.bottomRight, 1, 1), // 右下角
      _buildEdgeHandle(Alignment.topCenter, 0, -1), // 顶部
      _buildEdgeHandle(Alignment.bottomCenter, 0, 1), // 底部
      _buildEdgeHandle(Alignment.centerLeft, -1, 0), // 左边
      _buildEdgeHandle(Alignment.centerRight, 1, 0), // 右边
    ];
  }

  /// 创建 **角落** 拖拽手柄（调整宽高）
  Widget _buildHandle(Alignment alignment, double dxFactor, double dyFactor) {
    return SizedBox(
      width: annotation.width,
      height: annotation.height,
      child: Align(
        alignment: alignment,
        child: MouseRegion(
          cursor: SystemMouseCursors.click,
          child: GestureDetector(
            onPanUpdate: (details) {
              // onSizeChanged((annotation.position.dx, annotation.position.dy));
              if (alignment == Alignment.topLeft) {
                onSizeChanged([
                  SizeChanged(
                    value: details.delta.dx,
                    type: SizeChangedType.left,
                  ),
                  SizeChanged(
                    value: details.delta.dy,
                    type: SizeChangedType.top,
                  ),
                ]);
              }
              if (alignment == Alignment.topRight) {
                onSizeChanged([
                  SizeChanged(
                    value: details.delta.dx,
                    type: SizeChangedType.right,
                  ),
                  SizeChanged(
                    value: details.delta.dy,
                    type: SizeChangedType.top,
                  ),
                ]);
              }
              if (alignment == Alignment.bottomLeft) {
                onSizeChanged([
                  SizeChanged(
                    value: details.delta.dx,
                    type: SizeChangedType.left,
                  ),
                  SizeChanged(
                    value: details.delta.dy,
                    type: SizeChangedType.bottom,
                  ),
                ]);
              }
              if (alignment == Alignment.bottomRight) {
                onSizeChanged([
                  SizeChanged(
                    value: details.delta.dx,
                    type: SizeChangedType.right,
                  ),
                  SizeChanged(
                    value: details.delta.dy,
                    type: SizeChangedType.bottom,
                  ),
                ]);
              }
            },
            child: Container(
              width: 16,
              height: 16,
              decoration: BoxDecoration(
                color: kDebugMode ? Colors.blue : Colors.transparent,
                shape: BoxShape.circle,
              ),
            ),
          ),
        ),
      ),
    );
  }

  /// 创建 **边框** 拖拽手柄（调整宽或高）
  Widget _buildEdgeHandle(
    Alignment alignment,
    double dxFactor,
    double dyFactor,
  ) {
    MouseCursor cursor;
    switch (alignment) {
      case Alignment.topCenter:
        cursor = SystemMouseCursors.resizeUp;
        break;
      case Alignment.bottomCenter:
        cursor = SystemMouseCursors.resizeDown;
        break;
      case Alignment.centerLeft:
        cursor = SystemMouseCursors.resizeLeft;
        break;
      case Alignment.centerRight:
        cursor = SystemMouseCursors.resizeRight;
      default:
        cursor = SystemMouseCursors.basic;
    }
    return SizedBox(
      width: annotation.width,
      height: annotation.height,
      child: Align(
        alignment: alignment,
        child: MouseRegion(
          cursor: cursor,
          child: GestureDetector(
            onPanUpdate: (details) {
              if (alignment == Alignment.centerLeft) {
                onSizeChanged([
                  SizeChanged(
                    type: SizeChangedType.left,
                    value: details.delta.dx,
                  ),
                ]);
              }
              if (alignment == Alignment.topCenter) {
                onSizeChanged([
                  SizeChanged(
                    type: SizeChangedType.top,
                    value: details.delta.dy,
                  ),
                ]);
              }
              if (alignment == Alignment.bottomCenter) {
                onSizeChanged([
                  SizeChanged(
                    type: SizeChangedType.bottom,
                    value: details.delta.dy,
                  ),
                ]);
              }

              if (alignment == Alignment.centerRight) {
                onSizeChanged([
                  SizeChanged(
                    type: SizeChangedType.right,
                    value: details.delta.dx,
                  ),
                ]);
              }
            },
            child: Container(
              width: dxFactor == 0 ? annotation.width - 16 : 3,
              height: dyFactor == 0 ? annotation.height - 16 : 3,
              color: kDebugMode ? Colors.yellow : Colors.transparent, // 透明手柄
            ),
          ),
        ),
      ),
    );
  }
}
