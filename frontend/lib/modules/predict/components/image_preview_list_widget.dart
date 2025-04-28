import 'package:auto_ml/modules/predict/models/image_preview_model.dart';
import 'package:flutter/material.dart';

class ImagePreviewListWidget extends StatefulWidget {
  const ImagePreviewListWidget({
    super.key,
    required this.images,
    required this.onSelected,
  });
  final List<ImagePreviewModel> images;
  final void Function(ImagePreviewModel model) onSelected;

  @override
  State<ImagePreviewListWidget> createState() => _ImagePreviewListWidgetState();
}

class _ImagePreviewListWidgetState extends State<ImagePreviewListWidget> {
  @override
  Widget build(BuildContext context) {
    return Material(
      borderRadius: BorderRadius.circular(10),
      elevation: 10,
      child: Container(
        padding: EdgeInsets.all(5),
        height: 110,
        width: double.infinity,
        decoration: BoxDecoration(borderRadius: BorderRadius.circular(10)),
        child: ListView.separated(
          itemBuilder: (c, i) {
            return InkWell(
              onTap: () {
                widget.onSelected(widget.images[i]);
              },
              child: Container(
                width: 100,
                height: 100,
                decoration: BoxDecoration(
                  borderRadius: BorderRadius.circular(4),
                  image: DecorationImage(
                    image: Image.network(widget.images[i].url).image,
                  ),
                ),
              ),
            );
          },
          separatorBuilder: (c, i) => SizedBox(width: 10),
          itemCount: widget.images.length,
        ),
      ),
    );
  }
}
