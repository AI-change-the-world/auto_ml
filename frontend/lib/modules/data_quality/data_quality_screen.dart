import 'dart:async';
import 'dart:convert';
import 'dart:typed_data';

import 'package:auto_ml/api.dart';
import 'package:auto_ml/common/sse/sse.dart';
import 'package:auto_ml/utils/styles.dart';
import 'package:file_selector/file_selector.dart';
import 'package:flutter/material.dart';
import 'package:markdown_widget/widget/markdown.dart';

class DataQualityScreen extends StatefulWidget {
  const DataQualityScreen({super.key});

  @override
  State<DataQualityScreen> createState() => _DataQualityScreenState();
}

class _DataQualityScreenState extends State<DataQualityScreen> {
  static const XTypeGroup typeGroup = XTypeGroup(
    label: 'images',
    extensions: <String>['jpg', 'jpeg', 'png'],
  );

  final StreamController<String> ss = StreamController.broadcast();

  String llmData = "";

  @override
  void dispose() {
    ss.close();
    super.dispose();
  }

  @override
  void initState() {
    super.initState();
    ss.stream.listen((event) {
      if (!event.contains("[DONE]")) {
        setState(() {
          llmData += event;
        });
      }
    });
  }

  // ignore: avoid_init_to_null
  Uint8List? image = null;

  // ignore: avoid_init_to_null
  Uint8List? targetImage = null;
  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsetsGeometry.all(10),
      child: Row(
        children: [
          Expanded(
            flex: 1,
            child: Container(
              height: double.infinity,
              padding: EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: Colors.grey[200],
                borderRadius: BorderRadius.circular(4),
              ),
              child: SingleChildScrollView(
                child: Column(
                  spacing: 10,

                  children: [
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
                          Text(
                            'Target Image: ',
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
                          targetImage = await file.readAsBytes();
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
                            targetImage == null
                                ? Center(child: Icon(Icons.add, size: 50))
                                : Image.memory(targetImage!),
                      ),
                    ),

                    SizedBox(height: 20),
                    SizedBox(
                      height: 30,
                      child: Row(
                        children: [
                          Spacer(),
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
                              if (image == null || targetImage == null) {
                                return;
                              }
                              String base64Image = base64Encode(image!);
                              String base64TargetImage = base64Encode(
                                targetImage!,
                              );

                              sse(Api.measure, {
                                "img1": base64Image,
                                "img2": base64TargetImage,
                                "model_id": 4,
                              }, ss);
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
          SizedBox(width: 20),
          Expanded(
            flex: 3,
            child: Container(
              height: double.infinity,
              padding: EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: Colors.grey[200],
                borderRadius: BorderRadius.circular(4),
              ),
              width: double.infinity,
              child: MarkdownWidget(data: llmData),
            ),
          ),
        ],
      ),
    );
  }
}
