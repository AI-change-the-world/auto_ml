import 'package:auto_ml/modules/isar/dataset.dart';
import 'package:flutter/material.dart';

class _CardState {
  final double xRotation;
  final double yRotation;
  final bool showIcon;

  const _CardState({
    this.xRotation = 0,
    this.yRotation = 0,
    this.showIcon = false,
  });

  @override
  bool operator ==(Object other) {
    if (identical(this, other)) return true;

    return other is _CardState &&
        other.xRotation == xRotation &&
        other.yRotation == yRotation &&
        other.showIcon == showIcon;
  }

  @override
  int get hashCode =>
      xRotation.hashCode ^ yRotation.hashCode ^ showIcon.hashCode;

  _CardState copyWith({double? xRotation, double? yRotation, bool? showIcon}) {
    return _CardState(
      xRotation: xRotation ?? this.xRotation,
      yRotation: yRotation ?? this.yRotation,
      showIcon: showIcon ?? this.showIcon,
    );
  }
}

class DatasetCard extends StatefulWidget {
  const DatasetCard({super.key, required this.dataset});
  final Dataset dataset;

  @override
  State<DatasetCard> createState() => _DatasetCardState();
}

class _DatasetCardState extends State<DatasetCard> {
  late ValueNotifier<_CardState> _cardState;
  final double maxAngle = 0.15; // 最大旋转角度（弧度）

  @override
  void initState() {
    super.initState();
    _cardState = ValueNotifier(_CardState());
  }

  @override
  void dispose() {
    _cardState.dispose();
    super.dispose();
  }

  void _updateRotation(Offset position, Size size) {
    double dx = (position.dx - size.width / 2) / (size.width / 2); // -1 ~ 1
    double dy = (position.dy - size.height / 2) / (size.height / 2); // -1 ~ 1

    // 计算旋转角度，映射到 [-maxAngle, maxAngle]
    double newXRotation = dy * -maxAngle;
    double newYRotation = dx * maxAngle;
    _CardState newState = _cardState.value.copyWith(
      xRotation: newXRotation, // 控制前后倾斜
      yRotation: newYRotation, // 控制左右倾斜
    );
    if (_cardState.value != newState) {
      _cardState.value = newState;
    }
  }

  @override
  Widget build(BuildContext context) {
    return ValueListenableBuilder(
      valueListenable: _cardState,
      builder: (c, s, _) {
        return MouseRegion(
          onEnter: (event) {
            _cardState.value = _CardState(showIcon: true);
          },
          onHover: (event) {
            final RenderBox box = context.findRenderObject() as RenderBox;
            final Offset localPosition = box.globalToLocal(event.position);
            _updateRotation(localPosition, box.size);
          },
          onExit: (_) => _cardState.value = _CardState(),
          child: Transform(
            alignment: Alignment.center,
            transform:
                Matrix4.identity()
                  ..setEntry(3, 2, 0.0015) // 透视效果
                  ..rotateX(s.xRotation)
                  ..rotateY(s.yRotation),
            child: Container(
              width: 200,
              height: 150,
              decoration: BoxDecoration(
                color: widget.dataset.type.color,
                borderRadius: BorderRadius.circular(20),
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withValues(alpha: 0.2),
                    blurRadius: 10,
                    spreadRadius: 2,
                    offset: Offset(-s.yRotation * 20, s.xRotation * 20),
                  ),
                ],
              ),

              child: Stack(
                children: [
                  Center(
                    child: Text(
                      widget.dataset.name ?? "Unknown",
                      style: TextStyle(fontSize: 20, color: Colors.white),
                    ),
                  ),
                  if (s.showIcon)
                    Positioned(
                      bottom: 10,
                      right: 10,
                      child: widget.dataset.type.icon(
                        color: iconColor,
                        size: iconSize,
                      ),
                    ),
                ],
              ),
            ),
          ),
        );
      },
    );
  }

  double iconSize = 18;
  Color iconColor = Colors.white;
}
