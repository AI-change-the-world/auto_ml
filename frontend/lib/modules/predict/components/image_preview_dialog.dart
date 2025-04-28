import 'package:auto_ml/common/dialog_wrapper.dart';
import 'package:auto_ml/modules/predict/components/image_preview_list_widget.dart';
import 'package:auto_ml/modules/predict/notifier/image_preview_notifier.dart';
import 'package:auto_ml/utils/logger.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class ImagePreviewDialog extends ConsumerStatefulWidget {
  const ImagePreviewDialog({super.key, required this.fileId});
  final int fileId;

  @override
  ConsumerState<ImagePreviewDialog> createState() => _ImagePreviewDialogState();
}

class _ImagePreviewDialogState extends ConsumerState<ImagePreviewDialog> {
  late Stream<String> stream =
      ref.read(imagePreviewProvider(widget.fileId).notifier).stream;
  @override
  void initState() {
    super.initState();
    stream.listen((v) {
      logger.i(v);
      if (v.contains("[DONE]")) {
        ref.read(imagePreviewProvider(widget.fileId).notifier).setDone();
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(imagePreviewProvider(widget.fileId));
    return dialogWrapper(
      child: Column(
        children: [
          Expanded(
            child: Builder(
              builder: (c) {
                if (state.loading) {
                  return const Center(child: CircularProgressIndicator());
                }
                return Container();
              },
            ),
          ),
          ImagePreviewListWidget(images: [], onSelected: (model) {}),
        ],
      ),
      width: MediaQuery.of(context).size.width * 0.8,
      height: MediaQuery.of(context).size.height * 0.8,
    );
  }
}
