import 'package:auto_ml/modules/annotation/models/annotation.dart';
import 'package:auto_ml/modules/annotation/models/changed.dart';
import 'package:auto_ml/modules/annotation/notifiers/annotation_notifier.dart';
import 'package:auto_ml/utils/logger.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class AnnotationWidget extends ConsumerWidget {
  const AnnotationWidget({
    super.key,
    required this.uuid,

    required this.classes,
  });

  final String uuid;

  final List<String> classes;
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    logger.i("[annotation] build annotation, current: $uuid");
    final annotation = ref.watch(singleAnnotationProvider(uuid));

    if (!annotation.visible) {
      return SizedBox();
    }

    String label;

    try {
      label = classes[annotation.id];
    } catch (e) {
      label = "unknown";
    }

    return Positioned(
      left: annotation.position.dx,
      top: annotation.position.dy,
      child: GestureDetector(
        onPanUpdate: (details) {
          // onPanUpdate(details);
          ref
              .read(singleAnnotationProvider(uuid).notifier)
              .updateAnnotation(details: details);
        },
        onTap: () {
          // onSelected();
          ref
              .read(annotationContainerProvider.notifier)
              .changeCurrentAnnotation(uuid);
        },
        child: Stack(
          children: [
            // 标注框
            MouseRegion(
              cursor: SystemMouseCursors.grab,
              child: Material(
                color: Colors.transparent,
                elevation: annotation.selected ? 4 : 0,
                child: Container(
                  width: annotation.width,
                  height: annotation.height,
                  decoration: BoxDecoration(
                    color: Colors.red.withValues(alpha: 0.3),
                    border: Border.all(
                      color: !annotation.editable ? Colors.grey : Colors.red,
                      width: 2,
                    ),
                  ),
                  child: Align(
                    alignment: Alignment.topLeft,
                    child: Padding(
                      padding: EdgeInsets.only(top: 1, left: 1),
                      child: Text(
                        label,
                        style: TextStyle(
                          fontSize: 8,
                          color: Colors.white,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ),
                  ),
                ),
              ),
            ),
            // 角落 & 边框手柄
            ..._buildResizeHandles(annotation, ref),
          ],
        ),
      ),
    );
  }

  /// 构建 8 个拖拽手柄
  List<Widget> _buildResizeHandles(Annotation annotation, WidgetRef ref) {
    return [
      _buildHandle(Alignment.topLeft, annotation, ref), // 左上角
      _buildHandle(Alignment.topRight, annotation, ref), // 右上角
      _buildHandle(Alignment.bottomLeft, annotation, ref), // 左下角
      _buildHandle(Alignment.bottomRight, annotation, ref), // 右下角
      _buildEdgeHandle(Alignment.topCenter, annotation, ref), // 顶部
      _buildEdgeHandle(Alignment.bottomCenter, annotation, ref), // 底部
      _buildEdgeHandle(Alignment.centerLeft, annotation, ref), // 左边
      _buildEdgeHandle(Alignment.centerRight, annotation, ref), // 右边
    ];
  }

  /// 创建 **角落** 拖拽手柄（调整宽高）
  Widget _buildHandle(
    Alignment alignment,
    Annotation annotation,
    WidgetRef ref,
  ) {
    return SizedBox(
      width: annotation.width,
      height: annotation.height,
      child: Align(
        alignment: alignment,
        child: MouseRegion(
          cursor:
              alignment == Alignment.bottomRight
                  ? SystemMouseCursors.resizeDownRight
                  : alignment == Alignment.bottomLeft
                  ? SystemMouseCursors.resizeDownLeft
                  : alignment == Alignment.topLeft
                  ? SystemMouseCursors.resizeUpLeft
                  : alignment == Alignment.topRight
                  ? SystemMouseCursors.resizeUpRight
                  : SystemMouseCursors.click,
          child: GestureDetector(
            onPanUpdate: (details) {
              if (!annotation.editable) {
                return;
              }
              // onSizeChanged((annotation.position.dx, annotation.position.dy));
              if (alignment == Alignment.topLeft) {
                ref
                    .read(singleAnnotationProvider(uuid).notifier)
                    .updateAnnotation(
                      sizeChanged: [
                        SizeChanged(
                          value: details.delta.dx,
                          type: SizeChangedType.left,
                        ),
                        SizeChanged(
                          value: details.delta.dy,
                          type: SizeChangedType.top,
                        ),
                      ],
                    );
              }
              if (alignment == Alignment.topRight) {
                ref
                    .read(singleAnnotationProvider(uuid).notifier)
                    .updateAnnotation(
                      sizeChanged: [
                        SizeChanged(
                          value: details.delta.dx,
                          type: SizeChangedType.right,
                        ),
                        SizeChanged(
                          value: details.delta.dy,
                          type: SizeChangedType.top,
                        ),
                      ],
                    );
              }
              if (alignment == Alignment.bottomLeft) {
                ref
                    .read(singleAnnotationProvider(uuid).notifier)
                    .updateAnnotation(
                      sizeChanged: [
                        SizeChanged(
                          value: details.delta.dx,
                          type: SizeChangedType.left,
                        ),
                        SizeChanged(
                          value: details.delta.dy,
                          type: SizeChangedType.bottom,
                        ),
                      ],
                    );
              }
              if (alignment == Alignment.bottomRight) {
                ref
                    .read(singleAnnotationProvider(uuid).notifier)
                    .updateAnnotation(
                      sizeChanged: [
                        SizeChanged(
                          value: details.delta.dx,
                          type: SizeChangedType.right,
                        ),
                        SizeChanged(
                          value: details.delta.dy,
                          type: SizeChangedType.bottom,
                        ),
                      ],
                    );
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
    Annotation annotation,
    WidgetRef ref,
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
              if (!annotation.editable) {
                return;
              }

              if (alignment == Alignment.centerLeft) {
                ref
                    .read(singleAnnotationProvider(uuid).notifier)
                    .updateAnnotation(
                      sizeChanged: [
                        SizeChanged(
                          type: SizeChangedType.left,
                          value: details.delta.dx,
                        ),
                      ],
                    );
              }
              if (alignment == Alignment.topCenter) {
                ref
                    .read(singleAnnotationProvider(uuid).notifier)
                    .updateAnnotation(
                      sizeChanged: [
                        SizeChanged(
                          type: SizeChangedType.top,
                          value: details.delta.dy,
                        ),
                      ],
                    );
              }
              if (alignment == Alignment.bottomCenter) {
                ref
                    .read(singleAnnotationProvider(uuid).notifier)
                    .updateAnnotation(
                      sizeChanged: [
                        SizeChanged(
                          type: SizeChangedType.bottom,
                          value: details.delta.dy,
                        ),
                      ],
                    );
              }

              if (alignment == Alignment.centerRight) {
                ref
                    .read(singleAnnotationProvider(uuid).notifier)
                    .updateAnnotation(
                      sizeChanged: [
                        SizeChanged(
                          type: SizeChangedType.right,
                          value: details.delta.dx,
                        ),
                      ],
                    );
              }
            },
            child: Container(
              width: alignment.x == 0 ? annotation.width - 16 : 3,
              height: alignment.y == 0 ? annotation.height - 16 : 3,
              color: kDebugMode ? Colors.yellow : Colors.transparent, // 透明手柄
            ),
          ),
        ),
      ),
    );
  }
}
