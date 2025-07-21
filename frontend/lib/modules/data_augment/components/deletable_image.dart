import 'package:auto_ml/modules/data_augment/models/cv_resp.dart';
import 'package:auto_ml/utils/styles.dart';
import 'package:flutter/material.dart';

class DeletableImage extends StatefulWidget {
  const DeletableImage({
    super.key,
    required this.resp,
    this.width = 256,
    this.height = 256,
    required this.onDelete,
  });
  final CvResp resp;
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
              widget.resp.presignUrl ?? "",
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
            Positioned(
              right: 10,
              bottom: 10,
              child: Container(
                padding: EdgeInsets.all(4),

                decoration: BoxDecoration(
                  color: Colors.grey,
                  borderRadius: BorderRadius.circular(4),
                ),
                child: Text(
                  widget.resp.score.toString(),
                  style: Styles.defaultButtonTextStyle.copyWith(
                    color: Colors.white,
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
