// ignore_for_file: avoid_init_to_null

import 'package:auto_ml/modules/predict/notifier/describe_images_notifier.dart';
import 'package:auto_ml/modules/predict/notifier/image_preview_notifier.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:gpt_markdown/gpt_markdown.dart';

class SidebarWidget extends ConsumerStatefulWidget {
  const SidebarWidget({super.key, required this.fileId});
  final int fileId;

  @override
  ConsumerState<SidebarWidget> createState() => _SidebarWidgetState();
}

class _SidebarWidgetState extends ConsumerState<SidebarWidget> {
  late Image? image = null;

  @override
  void initState() {
    super.initState();
  }

  late String totalData = "";

  @Deprecated("")
  loadImage(Rect rect) {
    Future.microtask(() async {
      image = await ref
          .read(imagePreviewProvider(widget.fileId).notifier)
          .cropImage(rect);
      setState(() {});
    });
  }

  // @override
  // void didUpdateWidget(covariant SidebarWidget oldWidget) {
  //   super.didUpdateWidget(oldWidget);
  //   final rect = ref.read(
  //     imagePreviewProvider(widget.fileId).select((value) => value.selected),
  //   );
  //   if (rect != null) {
  //     loadImage(rect);
  //   }
  // }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.all(10),
      child: SingleChildScrollView(
        controller: ref.read(describeImagesProvider.notifier).scrollController,
        child: GptMarkdown(ref.watch(describeImagesProvider)),
      ),
    );
  }
}
