import 'dart:async';
import 'dart:convert';
import 'dart:typed_data';

import 'package:auto_ml/api.dart';
import 'package:auto_ml/common/dialog_wrapper.dart';
import 'package:auto_ml/modules/data_augment/utils.dart';
import 'package:auto_ml/utils/styles.dart';
import 'package:auto_ml/utils/toast_utils.dart';
import 'package:basic_dropdown_button/basic_dropwon_button_widget.dart';
import 'package:basic_dropdown_button/custom_dropdown_button.dart';
import 'package:file_selector/file_selector.dart';
import 'package:flutter/material.dart';

import '../../../common/sse/sse.dart';

class CvDialog extends StatefulWidget {
  const CvDialog({super.key});

  @override
  State<CvDialog> createState() => _CvDialogState();
}

class _CvDialogState extends State<CvDialog> {
  int generateCount = 5;
  final StreamController<String> ss = StreamController.broadcast();
  List<String> images = [];

  static const XTypeGroup typeGroup = XTypeGroup(
    label: 'images',
    extensions: <String>['jpg', 'jpeg', 'png'],
  );

  // ignore: avoid_init_to_null
  Uint8List? image = null;

  @override
  void initState() {
    super.initState();
    ss.stream.listen((event) {
      if (event.contains("[DONE]")) {
        ToastUtils.success(null, title: "Generated done");
      }
      if (event.startsWith("path:") && event.contains("png")) {
        String url = event.split(":")[1];
        Future.microtask(() async {
          final s = await getPresignUrl(url);
          images.add(s);
          setState(() {});
        });
      }
    });
  }

  @override
  void dispose() {
    ss.close();
    super.dispose();
  }

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
                padding: EdgeInsets.all(10),
                decoration: BoxDecoration(color: Colors.grey[200]),
                child: Column(
                  children: [
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
                                  [5, 10, 15, 20]
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
                                            fixedSize: WidgetStateProperty.all(
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
                                                borderRadius: BorderRadius.zero,
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
                              if (image == null) {
                                return;
                              }

                              setState(() {
                                images.clear();
                              });

                              Map<String, dynamic> data = {
                                "count": generateCount,
                                "b64": base64.encode(image!),
                              };
                              sse(Api.cv, data, ss);
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
                              (v) => Image.network(v, width: 256, height: 256),
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
