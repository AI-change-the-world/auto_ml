import 'dart:async';
import 'dart:typed_data';

import 'package:auto_ml/api.dart';
import 'package:auto_ml/common/dialog_wrapper.dart';
import 'package:auto_ml/common/sse/sse.dart';
import 'package:auto_ml/utils/logger.dart';
import 'package:auto_ml/utils/styles.dart';
import 'package:auto_ml/utils/toast_utils.dart';
import 'package:basic_dropdown_button/basic_dropwon_button_widget.dart';
import 'package:basic_dropdown_button/custom_dropdown_button.dart';
import 'package:dio/dio.dart';
import 'package:file_selector/file_selector.dart';
import 'package:flutter/material.dart';

class SdDialog extends StatefulWidget {
  const SdDialog({super.key});

  @override
  State<SdDialog> createState() => _SdDialogState();
}

class _SdDialogState extends State<SdDialog> {
  int generateCount = 1;
  final StreamController<String> ss = StreamController.broadcast();
  List<String> images = [];

  static const XTypeGroup typeGroup = XTypeGroup(
    label: 'images',
    extensions: <String>['jpg', 'jpeg', 'png'],
  );

  // ignore: avoid_init_to_null
  Uint8List? image = null;

  late final TextEditingController _promptController = TextEditingController();

  @override
  void initState() {
    super.initState();
    ss.stream.listen((event) {
      logger.d("event. $event");

      if (event.contains("[DONE]")) {
        ToastUtils.success(null, title: "Generated done");
      }
      if (event.contains("https")) {
        images.add(event.replaceAll("\n", "").trim());
        setState(() {});
      }
    });
  }

  @override
  void dispose() {
    ss.close();
    _promptController.dispose();
    super.dispose();
  }

  late final Dio _dio = Dio();

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
                height: double.infinity,
                padding: EdgeInsets.all(10),
                decoration: BoxDecoration(color: Colors.grey[200]),
                child: SingleChildScrollView(
                  child: Column(
                    spacing: 10,

                    children: [
                      SizedBox(
                        height: 30,
                        child: Row(
                          children: [
                            Text(
                              'Input Prompt: ',
                              style: TextStyle(
                                fontSize: 16,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                            Spacer(),
                            Tooltip(
                              message: "Prompt 优化",
                              child: InkWell(
                                onTap: () async {
                                  if (_promptController.text.trim().isEmpty) {
                                    return;
                                  }
                                  Map<String, dynamic> data = {
                                    "model_id": 4,
                                    "prompt": _promptController.text,
                                  };

                                  await _dio
                                      .post(Api.optimize, data: data)
                                      .then((r) {
                                        if (r.data == null) {
                                          ToastUtils.error(
                                            null,
                                            title: "Optimization error",
                                          );
                                          return;
                                        }

                                        if (r.data["status"] == 200) {
                                          ToastUtils.success(
                                            null,
                                            title: "Optimization done",
                                          );
                                          _promptController.text =
                                              r.data["data"]["prompt"];
                                        }
                                      });
                                },
                                child: Icon(Icons.generating_tokens),
                              ),
                            ),
                          ],
                        ),
                      ),
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
                          hintStyle: TextStyle(
                            fontSize: 12,
                            color: Colors.grey,
                          ),
                        ),
                      ),
                      SizedBox(
                        height: 30,
                        child: Row(
                          children: [
                            Text(
                              'Reference Image: ',
                              style: TextStyle(
                                fontSize: 16,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                            Spacer(),
                          ],
                        ),
                      ),
                      InkWell(
                        onTap: () async {
                          final file = await openFile(
                            acceptedTypeGroups: [typeGroup],
                          );
                          if (file != null) {
                            image = await file.readAsBytes();
                            setState(() {});
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
                              image == null
                                  ? Center(child: Icon(Icons.add, size: 50))
                                  : Image.memory(image!),
                        ),
                      ),

                      SizedBox(height: 20),

                      SizedBox(
                        height: 30,
                        child: Row(
                          children: [
                            Spacer(),

                            Text(
                              "Generate Count: ",
                              style: Styles.defaultButtonTextStyle,
                            ),
                            SizedBox(
                              width: 80,
                              child: CustomDropDownButton<int>(
                                buttonIcon:
                                    ({required showedMenu}) => SizedBox(
                                      height: 30,
                                      // width: 30,
                                      child: Center(
                                        child: Icon(
                                          Icons.arrow_drop_down,
                                          color: Colors.black,
                                        ),
                                      ),
                                    ),
                                buttonIconFirst: false,
                                buttonStyle: ButtonStyle(
                                  fixedSize: WidgetStateProperty.all(
                                    Size(100, 20),
                                  ),
                                  backgroundColor: WidgetStatePropertyAll(
                                    Colors.grey[300],
                                  ),
                                  padding: WidgetStatePropertyAll(
                                    const EdgeInsets.symmetric(
                                      horizontal: 16,
                                      vertical: 12,
                                    ),
                                  ),
                                  textStyle: WidgetStatePropertyAll(
                                    const TextStyle(
                                      color: Colors.white,
                                      fontWeight: FontWeight.w400,
                                    ),
                                  ),
                                  shape: WidgetStatePropertyAll(
                                    RoundedRectangleBorder(
                                      borderRadius: BorderRadius.circular(4.0),
                                    ),
                                  ),
                                ),
                                buttonText: generateCount.toString(),
                                position: DropDownButtonPosition.bottomCenter,
                                buttonIconColor: Colors.black,
                                buttonTextStyle: Styles.defaultButtonTextStyle,
                                menuItems:
                                    [1, 2, 3]
                                        .map(
                                          (e) => CustomDropDownButtonItem(
                                            value: e,
                                            text: e.toString(),
                                            onPressed: () {
                                              if (e != generateCount) {
                                                setState(() {
                                                  generateCount = e;
                                                });
                                              }
                                            },
                                            buttonStyle: ButtonStyle(
                                              fixedSize:
                                                  WidgetStateProperty.all(
                                                    Size(100, 20),
                                                  ),
                                              backgroundColor:
                                                  WidgetStatePropertyAll(
                                                    Colors.grey[300],
                                                  ),
                                              textStyle: WidgetStatePropertyAll(
                                                const TextStyle(
                                                  color: Colors.black,
                                                  fontSize: 12,
                                                ),
                                              ),
                                              shape: WidgetStatePropertyAll(
                                                RoundedRectangleBorder(
                                                  borderRadius:
                                                      BorderRadius.zero,
                                                ),
                                              ),
                                            ),
                                            textStyle: TextStyle(
                                              color: Colors.black,
                                              fontSize: 12,
                                            ),
                                          ),
                                        )
                                        .toList(),
                                menuBorderRadius: BorderRadius.circular(8),
                                selectedValue: generateCount,
                              ),
                            ),
                            const SizedBox(width: 10),
                            ElevatedButton(
                              style: ElevatedButton.styleFrom(
                                shape: RoundedRectangleBorder(
                                  borderRadius: BorderRadius.circular(
                                    4,
                                  ), // 设置圆角半径
                                ),
                                padding: EdgeInsets.symmetric(
                                  horizontal: 6,
                                  vertical: 3,
                                ), // 调整按钮大小
                              ),
                              onPressed: () {
                                if (_promptController.text.isEmpty) {
                                  return;
                                }

                                Map<String, dynamic> data = {
                                  "count": generateCount,
                                  "prompt": _promptController.text,
                                };
                                sse(Api.sd, data, ss);
                              },
                              child: Text(
                                "Submit",
                                style: Styles.defaultButtonTextStyle,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),
            Expanded(
              flex: 3,
              child: SingleChildScrollView(
                padding: EdgeInsets.all(10),
                child: SizedBox(
                  width: double.infinity,
                  child: Wrap(
                    runAlignment: WrapAlignment.start,
                    alignment: WrapAlignment.start,
                    spacing: 10,
                    runSpacing: 10,
                    children:
                        images
                            .map(
                              (v) => Image.network(v, width: 512, height: 512),
                            )
                            .toList(),
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
