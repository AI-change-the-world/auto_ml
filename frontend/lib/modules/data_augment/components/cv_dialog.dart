import 'dart:async';
import 'dart:convert';
import 'dart:typed_data';

import 'package:auto_ml/api.dart';
import 'package:auto_ml/common/dialog_wrapper.dart';
import 'package:auto_ml/modules/data_augment/common.dart';
import 'package:auto_ml/modules/data_augment/components/deletable_image.dart';
import 'package:auto_ml/modules/data_augment/models/cv_resp.dart';
import 'package:auto_ml/modules/data_augment/utils.dart';
import 'package:auto_ml/utils/styles.dart';
import 'package:auto_ml/utils/toast_utils.dart';
import 'package:basic_dropdown_button/basic_dropwon_button_widget.dart';
import 'package:basic_dropdown_button/custom_dropdown_button.dart';
import 'package:choice/choice.dart';
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
  List<CvResp> images = [];

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
        return;
      }
      if (event.contains("[Error]")) {
        ToastUtils.error(null, title: "Generated failed");
        return;
      }
      if (event.startsWith("path:") && event.contains("png")) {
        String s = event.replaceFirst("path:", "");
        Map<String, dynamic> map = jsonDecode(s);
        if (map["img_url"] == null) {
          return;
        }
        CvResp cvResp = CvResp.fromJson(map);

        String url = cvResp.imgUrl;
        Future.microtask(() async {
          final s = await getPresignUrl(url);
          cvResp.presignUrl = s;
          images.add(cvResp);
          setState(() {});
        });
      }
    });
  }

  @override
  void dispose() {
    ss.close();
    controller.dispose();
    super.dispose();
  }

  List<String> multipleSelected = [];
  final ExpansibleController controller = ExpansibleController();

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
                child: SingleChildScrollView(
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
                      Expansible(
                        headerBuilder:
                            (c, a) => Row(
                              children: [
                                Text(
                                  "Augment Types:",
                                  style: Styles.defaultButtonTextStyle,
                                ),
                                SizedBox(width: 5),
                                multipleSelected.isEmpty
                                    ? Expanded(
                                      child: Text(
                                        "None",
                                        style: Styles.defaultButtonTextStyle,
                                      ),
                                    )
                                    : Expanded(
                                      child: Tooltip(
                                        message: multipleSelected.join(", "),
                                        child: Text(
                                          multipleSelected.join(", "),
                                          maxLines: 1,
                                          overflow: TextOverflow.ellipsis,
                                          style:
                                              Styles.defaultButtonTextStyleGrey,
                                        ),
                                      ),
                                    ),

                                InkWell(
                                  onTap: () {
                                    if (controller.isExpanded) {
                                      controller.collapse();
                                    } else {
                                      controller.expand();
                                    }
                                  },
                                  child:
                                      controller.isExpanded
                                          ? Transform.rotate(
                                            angle: 3.14 / 2,
                                            child: Icon(
                                              Icons.arrow_back,
                                              size: Styles.datatableIconSize,
                                              color: Colors.grey,
                                            ),
                                          )
                                          : Transform.rotate(
                                            angle: -3.14 / 2,
                                            child: Icon(
                                              Icons.arrow_back,
                                              size: Styles.datatableIconSize,
                                              color: Colors.grey,
                                            ),
                                          ),
                                ),
                              ],
                            ),
                        bodyBuilder:
                            (c, a) => InlineChoice<String>(
                              multiple: true,
                              clearable: true,
                              value: multipleSelected,
                              onChanged: (v) {
                                setState(() => multipleSelected = v);
                              },
                              itemCount: AugmentConfigs.cvAugmentTypes.length,
                              itemBuilder: (selection, i) {
                                return ChoiceChip(
                                  labelStyle: Styles.defaultButtonTextStyle,
                                  selected: selection.selected(
                                    AugmentConfigs.cvAugmentTypes[i],
                                  ),
                                  onSelected: selection.onSelected(
                                    AugmentConfigs.cvAugmentTypes[i],
                                  ),
                                  label: Text(AugmentConfigs.cvAugmentTypes[i]),
                                );
                              },
                              listBuilder: ChoiceList.createWrapped(
                                spacing: 10,
                                runSpacing: 10,
                                padding: const EdgeInsets.symmetric(
                                  horizontal: 20,
                                  vertical: 25,
                                ),
                              ),
                            ),
                        controller: controller,
                      ),
                      SizedBox(height: 20),

                      SizedBox(
                        height: 30,
                        child: Row(
                          children: [
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
                            Spacer(),
                            // const SizedBox(width: 10),
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
                                  ToastUtils.error(
                                    context,
                                    title: "No image selected",
                                  );
                                  return;
                                }
                                if (multipleSelected.isEmpty) {
                                  ToastUtils.error(
                                    context,
                                    title: "No augment types selected",
                                  );
                                  return;
                                }

                                setState(() {
                                  images.clear();
                                });

                                Map<String, dynamic> data = {
                                  "count": generateCount,
                                  "b64": base64.encode(image!),
                                  "types": multipleSelected,
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
            ),
            Expanded(
              flex: 3,
              child: SizedBox(
                width: double.infinity,
                height: double.infinity,
                child: Column(
                  children: [
                    Expanded(
                      child: SingleChildScrollView(
                        padding: EdgeInsets.all(10),
                        child: Wrap(
                          runAlignment: WrapAlignment.start,
                          alignment: WrapAlignment.start,
                          spacing: 10,
                          runSpacing: 10,
                          children:
                              images
                                  .map(
                                    (v) => DeletableImage(
                                      resp: v,
                                      onDelete: () {
                                        images.remove(v);
                                        setState(() {});
                                      },
                                    ),
                                  )
                                  .toList(),
                        ),
                      ),
                    ),
                    const SizedBox(height: 20),
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
                              if (images.isEmpty) {
                                ToastUtils.error(
                                  context,
                                  title: "No image generated",
                                );
                                return;
                              }
                            },
                            child: Text(
                              "Save to ...",
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
          ],
        ),
      ),
    );
  }
}
