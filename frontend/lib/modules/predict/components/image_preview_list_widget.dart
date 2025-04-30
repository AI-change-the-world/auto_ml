import 'package:auto_ml/modules/predict/models/image_preview_model.dart';
import 'package:auto_ml/modules/predict/notifier/image_preview_notifier.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class ImagePreviewListWidget extends StatefulWidget {
  const ImagePreviewListWidget({
    super.key,
    required this.images,
    required this.onSelected,
    required this.id,
  });
  final List<ImagePreviewModel> images;
  final void Function(ImagePreviewModel model) onSelected;
  final int id;

  @override
  State<ImagePreviewListWidget> createState() => _ImagePreviewListWidgetState();
}

class _ImagePreviewListWidgetState extends State<ImagePreviewListWidget> {
  @override
  Widget build(BuildContext context) {
    return Material(
      borderRadius: BorderRadius.circular(10),
      elevation: 10,
      child: AnimatedContainer(
        padding: EdgeInsets.all(5),
        height: widget.images.isEmpty ? 0 : 110,
        width: double.infinity,
        decoration: BoxDecoration(borderRadius: BorderRadius.circular(10)),
        duration: Duration(milliseconds: 500),
        child: ListView.separated(
          scrollDirection: Axis.horizontal,
          itemBuilder: (c, i) {
            return InkWell(
              onTap: () {
                widget.onSelected(widget.images[i]);
              },
              child: _ImageListImage(
                index: i,
                id: widget.id,
                imageKey: widget.images[i].imageKey,
                url: widget.images[i].url,
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

class _ImageListImage extends ConsumerStatefulWidget {
  const _ImageListImage({
    required this.imageKey,
    required this.id,
    required this.index,
    required this.url,
  });
  final String imageKey;
  final String url;
  final int id;
  final int index;

  @override
  ConsumerState<_ImageListImage> createState() => __ImageListImageState();
}

class __ImageListImageState extends ConsumerState<_ImageListImage> {
  late String url = widget.url;

  @override
  void initState() {
    super.initState();
    if (widget.url.isEmpty) {
      Future.microtask(() {
        ref
            .read(imagePreviewProvider(widget.id).notifier)
            .getUrl(widget.imageKey)
            .then((v) {
              if (v != url) {
                setState(() {
                  url = v;
                });
                ref
                    .read(imagePreviewProvider(widget.id).notifier)
                    .updateImageUrl(widget.imageKey, v);
              }
            });
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 100,
      height: 100,
      decoration: BoxDecoration(
        color:
            ref.read(
                      imagePreviewProvider(widget.id).select((v) => v.current),
                    ) ==
                    widget.index
                ? Colors.lightBlueAccent
                : Colors.white,
        borderRadius: BorderRadius.circular(4),
        image:
            url.isNotEmpty
                ? DecorationImage(image: Image.network(url).image)
                : null,
      ),
      child: url.isEmpty ? Center(child: CircularProgressIndicator()) : null,
    );
  }
}
