import 'dart:convert';

import 'package:auto_ml/common/base_sse_response.dart';
import 'package:auto_ml/common/dialog_wrapper.dart';
import 'package:auto_ml/modules/predict/components/image_preview_list_widget.dart';
import 'package:auto_ml/modules/predict/components/sidebar_widget.dart';
import 'package:auto_ml/modules/predict/models/image_preview_model.dart';
import 'package:auto_ml/modules/predict/models/video_result.dart';
import 'package:auto_ml/modules/predict/notifier/image_preview_notifier.dart';
import 'package:auto_ml/utils/logger.dart';
import 'package:auto_ml/utils/toast_utils.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

const double _sidebarWidth = 400;

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
      if (v.contains("[DONE]")) {
        ref.read(imagePreviewProvider(widget.fileId).notifier).setDone();
        return;
      }
      try {
        final json = jsonDecode(v);
        SseResponse sseResponse = SseResponse.fromJson(json, (j) {
          String data = j.toString().replaceFirst("data:", "");
          if (data.contains("video_path")) {
            return VideoResult.fromJson(jsonDecode(data));
          }
          return data;
        });
        logger.i(sseResponse.message);
        logger.d(sseResponse.data.runtimeType);
        if (sseResponse.data is VideoResult) {
          ref
              .read(imagePreviewProvider(widget.fileId).notifier)
              .setData(sseResponse.data as VideoResult);
        } else {
          if (sseResponse.message != null) {
            ToastUtils.info(
              null,
              title:
                  sseResponse.message
                      .toString()
                      .replaceFirst("data:", "")
                      .trim(),
            );
          }
        }
      } catch (e, s) {
        logger.e(e);
        logger.e(s);
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(imagePreviewProvider(widget.fileId));
    return dialogWrapper(
      child: Column(
        spacing: 10,
        children: [
          Expanded(
            child: Builder(
              builder: (c) {
                if (state.loading) {
                  return const Center(child: CircularProgressIndicator());
                }
                if (state.current == -1) {
                  return Center(child: Text("Select a frame"));
                }
                return Row(
                  children: [
                    Expanded(
                      child: Center(
                        child: _buildCurrent(
                          state.images[state.current],
                          state.imageWidth,
                          state.imageHeight,
                          state.isSidebarOpen,
                        ),
                      ),
                    ),
                    AnimatedContainer(
                      decoration: BoxDecoration(
                        color: Colors.grey.shade200,
                        borderRadius: BorderRadius.only(
                          topLeft: Radius.circular(10),
                          bottomLeft: Radius.circular(10),
                        ),
                      ),
                      width: state.isSidebarOpen ? _sidebarWidth : 0,
                      height: double.infinity,
                      duration: Duration(milliseconds: 500),
                      child: SidebarWidget(fileId: widget.fileId),
                    ),
                  ],
                );
              },
            ),
          ),
          ImagePreviewListWidget(
            images: state.images,
            onSelected: (model) {
              ref
                  .read(imagePreviewProvider(widget.fileId).notifier)
                  .setCurrent(model);
            },
            id: widget.fileId,
          ),
        ],
      ),
      width: MediaQuery.of(context).size.width * 0.9,
      height: MediaQuery.of(context).size.height * 0.9,
    );
  }

  Widget _buildCurrent(
    ImagePreviewModel? model,
    double frameWidth,
    double frameHeight,
    bool isSidebarOpen,
  ) {
    if (model == null) {
      return const SizedBox();
    }

    final detections = model.detections;

    return SizedBox(
      width: frameWidth,
      height: frameHeight,
      child: InteractiveViewer(
        scaleEnabled: false,
        // boundaryMargin: boundaryMargin,
        boundaryMargin: EdgeInsets.all(0),
        constrained: false,
        child: SizedBox(
          width: frameWidth,
          height: frameHeight,
          child: Stack(
            children: [
              SizedBox(
                width: frameWidth,
                height: frameHeight,
                child: Image.network(model.url),
              ),
              ...detections.map((e) => _buildChild(e)),
            ],
          ),
        ),
      ),
    );
  }

  Positioned _buildChild(Detection e) {
    return Positioned(
      left: e.box.x1,
      top: e.box.y1,
      child: MouseRegion(
        cursor: SystemMouseCursors.click,
        child: GestureDetector(
          onTap: () {
            ref
                .read(imagePreviewProvider(widget.fileId).notifier)
                .showSidebar();

            Future.delayed(Duration(milliseconds: 500)).then((_) {
              ref
                  .read(imagePreviewProvider(widget.fileId).notifier)
                  .changeCurrentRect(
                    Rect.fromLTRB(e.box.x1, e.box.y1, e.box.x2, e.box.y2),
                  );
            });
          },
          child: Container(
            width: e.box.x2 - e.box.x1,
            height: e.box.y2 - e.box.y1,
            decoration: BoxDecoration(
              border: Border.all(color: Colors.white, width: 2),
              color: Colors.lightBlueAccent.withValues(alpha: 0.3),
            ),
            child: Align(
              alignment: Alignment.topLeft,
              child: Padding(
                padding: EdgeInsets.only(left: 5, top: 5),
                child: Text(
                  e.name,
                  style: TextStyle(
                    color: Colors.white,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
