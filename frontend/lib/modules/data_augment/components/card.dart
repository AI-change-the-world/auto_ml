import 'package:auto_ml/modules/dataset/components/left_right_background_container.dart';
import 'package:flutter/material.dart';

class Hover3DCard extends StatefulWidget {
  const Hover3DCard({
    super.key,
    required this.title,
    required this.description,
    required this.imageUrl,
    this.onTap,
    this.onDoubleTap,
  });

  final String title;
  final String description;
  final String imageUrl;
  final VoidCallback? onTap;
  final VoidCallback? onDoubleTap;

  @override
  State<Hover3DCard> createState() => _Hover3DCardState();
}

class _Hover3DCardState extends State<Hover3DCard> {
  final ValueNotifier<_CardState> _cardState = ValueNotifier(_CardState());
  final double maxAngle = 0.15;

  @override
  void dispose() {
    _cardState.dispose();
    super.dispose();
  }

  void _updateRotation(Offset position, Size size) {
    double dx = (position.dx - size.width / 2) / (size.width / 2);
    double dy = (position.dy - size.height / 2) / (size.height / 2);

    _cardState.value = _CardState(
      xRotation: dy * -maxAngle,
      yRotation: dx * maxAngle,
    );
  }

  @override
  Widget build(BuildContext context) {
    return ValueListenableBuilder(
      valueListenable: _cardState,
      builder: (context, s, _) {
        return MouseRegion(
          cursor: SystemMouseCursors.click,
          onHover: (event) {
            final box = context.findRenderObject() as RenderBox;
            _updateRotation(box.globalToLocal(event.position), box.size);
          },
          onExit: (_) => _cardState.value = const _CardState(),
          child: Transform(
            alignment: Alignment.center,
            transform:
                Matrix4.identity()
                  ..setEntry(3, 2, 0.0015)
                  ..rotateX(s.xRotation)
                  ..rotateY(s.yRotation),
            child: GestureDetector(
              onTap: widget.onTap,
              onDoubleTap: widget.onDoubleTap,
              child: _buildContent(),
            ),
          ),
        );
      },
    );
  }

  Widget _buildContent() {
    return LeftRightBackgroundContainer(
      width: 400,
      height: 300,
      rightBackgroundImage: widget.imageUrl,
      children: [
        Positioned(
          top: 20,
          left: 20,
          right: 20,
          child: Text(
            widget.title,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
            style: const TextStyle(
              fontSize: 20,
              fontWeight: FontWeight.bold,
              color: Colors.black,
              shadows: [Shadow(blurRadius: 4, color: Colors.black12)],
            ),
          ),
        ),
        Positioned(
          top: 60,
          left: 20,
          right: 20,
          child: Text(
            widget.description,
            maxLines: 3,
            overflow: TextOverflow.ellipsis,
            style: const TextStyle(
              fontSize: 14,
              color: Colors.black,
              shadows: [Shadow(blurRadius: 4, color: Colors.black12)],
            ),
          ),
        ),
      ],
    );
  }
}

class _CardState {
  final double xRotation;
  final double yRotation;

  const _CardState({this.xRotation = 0, this.yRotation = 0});
}
