import 'dart:async';
import 'dart:convert';

import 'package:auto_ml/api.dart';
import 'package:auto_ml/common/dialog_wrapper.dart';
import 'package:auto_ml/common/sse/sse.dart';
import 'package:auto_ml/modules/async_state_button.dart';
import 'package:auto_ml/modules/data_augment/models/cv_resp.dart';
import 'package:auto_ml/modules/data_augment/models/sd_deep_optimize_req.dart';
import 'package:auto_ml/modules/data_augment/models/sd_optimize_resp.dart';
import 'package:auto_ml/modules/data_augment/utils.dart';
import 'package:auto_ml/utils/styles.dart';
import 'package:auto_ml/utils/toast_utils.dart';
import 'package:flutter/material.dart';

class DeepEditDialog extends StatefulWidget {
  const DeepEditDialog({super.key, required this.cvResp});
  final CvResp cvResp;

  @override
  State<DeepEditDialog> createState() => _DeepEditDialogState();
}

class _DeepEditDialogState extends State<DeepEditDialog> {
  final TextEditingController _promptController = TextEditingController();
  final StreamController<String> ss = StreamController.broadcast();
  final GlobalKey<FutureStatusButtonSimpleState> _futureKey = GlobalKey();
  late String imgPath = widget.cvResp.imgUrl;
  late String presignedUrl = widget.cvResp.presignUrl!;

  @override
  void initState() {
    super.initState();
    ss.stream.listen((v) {
      if (v.contains("[DONE]")) {
        _futureKey.currentState?.changeCurrentState(FutureButtonState.initial);
      }

      if (v.contains("error")) {
        ToastUtils.error(null, title: "Generate error");
        _futureKey.currentState?.changeCurrentState(FutureButtonState.initial);
      }

      if (v.startsWith("path:") && v.contains("png")) {
        String s = v.replaceFirst("path:", "");
        Map<String, dynamic> map = jsonDecode(s);
        if (map["img"] == null) {
          return;
        }
        SdOptimizeResp cvResp = SdOptimizeResp.fromJson(map);

        String url = cvResp.img;
        Future.microtask(() async {
          final s = await getPresignUrl(url);
          cvResp.presignUrl = s;
          // images.add(cvResp);
          setState(() {
            list.add(cvResp);
          });
        });
      }
    });
  }

  @override
  void dispose() {
    _promptController.dispose();
    ss.close();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return dialogWrapper(
      width: MediaQuery.of(context).size.width * 0.9,
      height: MediaQuery.of(context).size.height * 0.9,
      child: Container(
        padding: EdgeInsets.all(10),
        child: Row(
          children: [
            Expanded(
              flex: 1,
              child: Container(
                height: double.infinity,
                padding: EdgeInsets.all(10),
                decoration: BoxDecoration(color: Colors.grey[200]),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      "Original image:",
                      style: Styles.defaultButtonTextStyle,
                    ),
                    SizedBox(height: 10),
                    Image.network(presignedUrl),
                    SizedBox(height: 20),
                    Text(
                      "Input optimization aims:",
                      style: Styles.defaultButtonTextStyle,
                    ),
                    SizedBox(height: 10),
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
                    SizedBox(height: 20),
                    // ElevatedButton(onPressed: () {}, child: Text("Submit")),
                    Row(
                      children: [
                        Spacer(),
                        FutureStatusButtonSimple(
                          key: _futureKey,
                          initialChild: Text(
                            "Submit",
                            style: Styles.defaultButtonTextStyle,
                          ),
                          onPressed: () {
                            if (_promptController.text.isEmpty) {
                              ToastUtils.error(
                                context,
                                title: "Prompt can't be empty",
                              );
                              return;
                            }
                            SdDeepOptimizeReq req = SdDeepOptimizeReq(
                              prompt: _promptController.text,
                              img: imgPath,
                            );

                            sse(Api.sdOptimize, req.toJson(), ss);
                            _futureKey.currentState!.changeCurrentState(
                              FutureButtonState.loading,
                            );
                          },
                        ),
                      ],
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

  List<SdOptimizeResp> list = [];

  Widget _buildLoopWidget() {
    return ListView.builder(
      itemCount: list.length,
      itemBuilder: (context, index) {
        return Padding(
          padding: const EdgeInsets.all(8.0),
          child: Material(
            elevation: 5,
            borderRadius: BorderRadius.circular(4),
            child: InkWell(
              onTap: () {
                setState(() {
                  presignedUrl = list[index].presignUrl!;
                  imgPath = list[index].img;
                });
              },
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
                    Image.network(list[index].presignUrl!),
                    SizedBox(width: 10),
                    Expanded(
                      child: Padding(
                        padding: EdgeInsets.only(left: 10),
                        child: Text(
                          list[index].tip,
                          style: TextStyle(fontSize: 16),
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        );
      },
    );
  }
}
