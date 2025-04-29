// ignore_for_file: avoid_init_to_null

import 'package:auto_ml/modules/predict/notifier/image_preview_notifier.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class SidebarWidget extends ConsumerStatefulWidget {
  const SidebarWidget({super.key, required this.fileId});
  final int fileId;

  @override
  ConsumerState<SidebarWidget> createState() => _SidebarWidgetState();
}

class _SidebarWidgetState extends ConsumerState<SidebarWidget> {
  late Image? image = null;

  loadImage(Rect rect) {
    Future.microtask(() async {
      image = await ref
          .read(imagePreviewProvider(widget.fileId).notifier)
          .cropImage(rect);
      setState(() {});
    });
  }

  @override
  Widget build(BuildContext context) {
    final rect = ref.watch(
      imagePreviewProvider(widget.fileId).select((value) => value.selected),
    );

    if (rect != null && image == null) {
      loadImage(rect);
    }

    return Padding(
      padding: EdgeInsets.all(10),
      child: Column(
        spacing: 10,
        mainAxisAlignment: MainAxisAlignment.start,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [if (image != null) image!],
      ),
    );
  }
}
