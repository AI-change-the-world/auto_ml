// ignore_for_file: avoid_init_to_null

import 'package:auto_ml/modules/predict/models/image_preview_model.dart';
import 'package:auto_ml/modules/predict/notifier/describe_images_notifier.dart';
import 'package:auto_ml/modules/predict/notifier/image_preview_notifier.dart';
import 'package:auto_ml/utils/styles.dart';
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
  @Deprecated("")
  late Image? image = null;

  late String imageDescription = "";
  late String imgKey = "";

  @override
  void initState() {
    super.initState();
  }

  late String totalData = "";

  @Deprecated("")
  void loadImage(Rect rect) {
    Future.microtask(() async {
      image = await ref
          .read(imagePreviewProvider(widget.fileId).notifier)
          .cropImage(rect);
      setState(() {});
    });
  }

  @override
  void didUpdateWidget(covariant SidebarWidget oldWidget) {
    super.didUpdateWidget(oldWidget);
    final index = ref.read(imagePreviewProvider(widget.fileId)).current;
    if (index == -1) {
      return;
    }
    final currentImage =
        ref.read(imagePreviewProvider(widget.fileId)).images[index];

    setState(() {
      imageDescription = currentImage.toResultString();
      imgKey = currentImage.imageKey;
    });
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(describeImagesProvider);

    return Padding(
      padding: EdgeInsets.all(10),
      child: Column(
        spacing: 10,
        children: [
          if (imageDescription.isNotEmpty) GptMarkdown(imageDescription),
          if (imageDescription.isNotEmpty)
            Align(
              alignment: Alignment.centerRight,
              child: Text(
                "(以上是由小模型生成的检测结果)",
                style: TextStyle(color: Colors.redAccent, fontSize: 12),
              ),
            ),
          SizedBox(
            height: 30,
            child: Row(
              children: [
                Spacer(),
                if (imageDescription.isNotEmpty)
                  ElevatedButton(
                    style: Styles.getDefaultButtonStyle(width: 150),
                    onPressed:
                        state.isGenerating
                            ? null
                            : () async {
                              ref
                                  .read(describeImagesProvider.notifier)
                                  .chatSingleFile([imgKey], imageDescription);
                            },
                    child: Text(
                      "Deep analysis",
                      style: Styles.defaultButtonTextStyle,
                    ),
                  ),
              ],
            ),
          ),
          Expanded(
            child: SingleChildScrollView(
              controller:
                  ref.read(describeImagesProvider.notifier).scrollController,
              child: GptMarkdown(state.data),
            ),
          ),
        ],
      ),
    );
  }
}
