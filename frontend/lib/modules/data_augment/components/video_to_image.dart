import 'dart:async';
import 'dart:convert';
import 'dart:typed_data';

import 'package:auto_ml/api.dart';
import 'package:auto_ml/common/dialog_wrapper.dart';
import 'package:auto_ml/common/sse/sse.dart';
import 'package:auto_ml/modules/async_state_button.dart';
import 'package:auto_ml/modules/data_augment/models/video_resp.dart';
import 'package:auto_ml/utils/logger.dart';
import 'package:auto_ml/utils/styles.dart';
import 'package:auto_ml/utils/toast_utils.dart';
import 'package:dio/dio.dart';
import 'package:file_selector/file_selector.dart';
import 'package:flutter/material.dart';
import 'package:media_kit/media_kit.dart';
import 'package:media_kit_video/media_kit_video.dart';

class VideoToImage extends StatefulWidget {
  const VideoToImage({super.key});

  @override
  State<VideoToImage> createState() => _VideoToImageState();
}

class _VideoToImageState extends State<VideoToImage> {
  static const XTypeGroup typeGroup = XTypeGroup(
    label: 'videos',
    extensions: <String>['mp4'],
  );

  final StreamController<String> ss = StreamController.broadcast();

  List<VideoResp> images = [];

  // ignore: avoid_init_to_null
  XFile? video = null;

  // Create a [Player] to control playback.
  late final player = Player();
  // Create a [VideoController] to handle video output from [Player].
  late final controller = VideoController(player);

  final GlobalKey<FutureStatusButtonSimpleState> buttonKey = GlobalKey();

  @override
  void initState() {
    super.initState();
    ss.stream.listen((event) {
      if (event.contains("[DONE]")) {
        ToastUtils.success(null, title: "Generated done");
        buttonKey.currentState?.changeCurrentState(FutureButtonState.initial);
        return;
      }
      if (event.contains("error")) {
        ToastUtils.error(null, title: "Something went wrong");
        buttonKey.currentState?.changeCurrentState(FutureButtonState.initial);
        return;
      }
      try {
        var entity = VideoResp.fromJson(jsonDecode(event));
        if (entity.frame != null) {
          images.add(entity);
          setState(() {});
        }
      } catch (e) {
        logger.e(e);
        // logger.i(event);
      }
    });
  }

  @override
  void dispose() {
    player.dispose();
    _promptController.dispose();
    super.dispose();
  }

  final _promptController = TextEditingController();

  @override
  Widget build(BuildContext context) {
    return dialogWrapper(
      width: MediaQuery.of(context).size.width * 0.9,
      height: MediaQuery.of(context).size.height * 0.9,
      child: Padding(
        padding: EdgeInsetsGeometry.all(10),
        child: Row(
          children: [
            Expanded(
              flex: 1,
              child: Container(
                height: MediaQuery.of(context).size.height * 0.9,
                padding: EdgeInsets.all(10),
                decoration: BoxDecoration(color: Colors.grey[200]),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  spacing: 10,
                  children: [
                    Text(
                      "Video to Image Converter",
                      style: Styles.defaultButtonTextStyle,
                    ),
                    InkWell(
                      onTap: () async {
                        final file = await openFile(
                          acceptedTypeGroups: [typeGroup],
                        );
                        if (file != null) {
                          setState(() {
                            video = file;
                          });
                        }
                      },
                      child: Container(
                        decoration: BoxDecoration(
                          color: Colors.grey[300],
                          borderRadius: BorderRadius.circular(4),
                        ),
                        width: double.infinity,
                        height: 200,
                        child:
                            video == null
                                ? Center(child: Icon(Icons.add, size: 50))
                                : FutureBuilder(
                                  future: Future(() async {
                                    if (tmpFilePath != null) {
                                      return;
                                    }
                                    final bytes = await video!.readAsBytes();
                                    player.open(await Media.memory(bytes));

                                    Future.microtask(() {
                                      _uploadFile(bytes);
                                    });
                                  }),
                                  builder: (c, s) {
                                    if (s.connectionState !=
                                        ConnectionState.done) {
                                      return const Center(
                                        child: CircularProgressIndicator(),
                                      );
                                    }

                                    return Video(controller: controller);
                                  },
                                ),
                      ),
                    ),
                    Text("Prompt", style: Styles.defaultButtonTextStyle),
                    TextField(
                      controller: _promptController,
                      style: TextStyle(fontSize: 12),
                      maxLines: 5,
                      decoration: InputDecoration(
                        contentPadding: EdgeInsets.only(
                          top: 10,
                          left: 10,
                          right: 10,
                        ),
                        border: OutlineInputBorder(),
                        focusedBorder: OutlineInputBorder(
                          borderSide: BorderSide(color: Colors.blueAccent),
                        ),
                        hintText: "prompt",
                        hintStyle: TextStyle(fontSize: 12, color: Colors.grey),
                      ),
                    ),
                    SizedBox(
                      height: 30,
                      child: Row(
                        children: [
                          Spacer(),
                          FutureStatusButtonSimple(
                            key: buttonKey,
                            initialChild: Text(
                              "Submit",
                              style: Styles.defaultButtonTextStyle,
                            ),
                            onPressed: () {
                              if (video == null ||
                                  tmpFilePath == null ||
                                  _promptController.text.isEmpty) {
                                ToastUtils.error(
                                  context,
                                  title: "Prompt or video is empty",
                                );
                                return;
                              }
                              Map<String, dynamic> data = {
                                "video_path": tmpFilePath,
                                "prompt": _promptController.text,
                              };

                              sse(Api.searchFrame, data, ss);
                              buttonKey.currentState!.changeCurrentState(
                                FutureButtonState.loading,
                              );
                            },
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            ),
            Expanded(flex: 3, child: _buildLoopWidget()),
          ],
        ),
      ),
    );
  }

  Widget _buildLoopWidget() {
    return ListView.builder(
      itemCount: images.length,
      itemBuilder: (context, index) {
        return Padding(
          padding: const EdgeInsets.all(8.0),
          child: Material(
            elevation: 5,
            borderRadius: BorderRadius.circular(4),
            child: Container(
              height: 300,
              padding: EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(4),
              ),
              margin: EdgeInsets.only(top: 5, bottom: 5),
              child: Row(
                children: [
                  Image.memory(base64Decode(images[index].frame!)),
                  SizedBox(width: 10),
                  Expanded(
                    child: Padding(
                      padding: EdgeInsets.only(left: 10),
                      child: Text(
                        "第${images[index].segmentIndex}部分, 第${images[index].frameIndex}帧, ${images[index].text}",
                        style: TextStyle(fontSize: 16),
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
        );
      },
    );
  }

  // ignore: avoid_init_to_null
  String? tmpFilePath = null;

  Future _uploadFile(Uint8List data) async {
    final client = Dio();
    final formData = FormData.fromMap({
      "video": MultipartFile.fromBytes(data, filename: "video.mp4"),
    });

    try {
      final response = await client.post(
        Api.upload,
        data: formData,
        options: Options(contentType: "multipart/form-data"),
      );
      logger.i("response.data ${response.data}");
      tmpFilePath = response.data["video_path"];

      if (tmpFilePath != null) {
        ToastUtils.success(null, title: "上传成功");
      } else {
        ToastUtils.error(null, title: "上传失败");
      }
    } catch (e) {
      logger.e(e);
      ToastUtils.error(null, title: "上传失败");
    }
  }
}
