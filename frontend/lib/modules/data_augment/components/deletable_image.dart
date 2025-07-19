import 'package:auto_ml/utils/styles.dart';
import 'package:flutter/material.dart';

class DeletableImage extends StatefulWidget {
  const DeletableImage({
    super.key,
    required this.url,
    this.width = 256,
    this.height = 256,
    required this.onDelete,
  });
  final String url;
  final double width;
  final double height;
  final VoidCallback onDelete;

  @override
  State<DeletableImage> createState() => _DeletableImageState();
}

class _DeletableImageState extends State<DeletableImage> {
  bool hover = false;

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        border: Border.all(color: hover ? Colors.grey : Colors.transparent),
        borderRadius: BorderRadius.circular(5),
        color: hover ? Colors.grey.shade200 : Colors.transparent,
      ),
      width: widget.width,
      height: widget.height,
      child: MouseRegion(
        onEnter: (event) {
          setState(() {
            hover = true;
          });
        },
        onExit: (event) {
          setState(() {
            hover = false;
          });
        },
        child: Stack(
          children: [
            Image.network(
              widget.url,
              width: widget.width,
              height: widget.height,
            ),
            if (hover)
              Positioned(
                right: 10,
                top: 10,
                child: InkWell(
                  onTap: () {
                    widget.onDelete();
                  },
                  child: Icon(
                    Icons.delete,
                    color: Colors.red,
                    size: Styles.datatableIconSize,
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }
}
