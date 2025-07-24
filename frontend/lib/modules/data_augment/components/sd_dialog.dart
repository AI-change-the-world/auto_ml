import 'dart:async';
import 'dart:convert';
import 'dart:typed_data';

import 'package:auto_ml/api.dart';
import 'package:auto_ml/common/dialog_wrapper.dart';
import 'package:auto_ml/common/sse/sse.dart';
import 'package:auto_ml/modules/async_state_button.dart';
import 'package:auto_ml/modules/data_augment/components/deep_edit_dialog.dart';
import 'package:auto_ml/modules/data_augment/components/editable_image.dart';
import 'package:auto_ml/modules/data_augment/models/cv_resp.dart';
import 'package:auto_ml/modules/data_augment/models/sd_augment_req.dart';
import 'package:auto_ml/modules/data_augment/models/sd_initialize_req.dart';
import 'package:auto_ml/modules/data_augment/notifiers/sd_client_on_notifier.dart';
import 'package:auto_ml/modules/data_augment/utils.dart';
import 'package:auto_ml/utils/logger.dart';
import 'package:auto_ml/utils/styles.dart';
import 'package:auto_ml/utils/toast_utils.dart';
import 'package:basic_dropdown_button/basic_dropwon_button_widget.dart';
import 'package:basic_dropdown_button/custom_dropdown_button.dart';
import 'package:dio/dio.dart';
import 'package:file_selector/file_selector.dart';
import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:file_type_dart/file_type_dart.dart';

class SdDialog extends StatefulWidget {
  const SdDialog({super.key});

  @override
  State<SdDialog> createState() => _SdDialogState();
}

class _SdDialogState extends State<SdDialog> {
  int generateCount = 1;
  final StreamController<String> ss = StreamController.broadcast();
  List<CvResp> images = [];

  static const XTypeGroup typeGroup = XTypeGroup(
    label: 'images',
    extensions: <String>['jpg', 'jpeg', 'png'],
  );

  // ignore: avoid_init_to_null
  Uint8List? image = null;

  late final TextEditingController _promptController = TextEditingController();
  final GlobalKey<FutureStatusButtonSimpleState> _buttonKey = GlobalKey();

  @override
  void initState() {
    super.initState();
    ss.stream.listen((event) {
      logger.d("event. $event");
      if (event.contains("error")) {
        Map m = jsonDecode(event);
        ToastUtils.error(null, title: m['message'] ?? "Unknow Error");
        _buttonKey.currentState!.changeCurrentState(FutureButtonState.initial);
        return;
      }

      if (event.contains("[DONE]")) {
        ToastUtils.success(null, title: "Generated done");
        _buttonKey.currentState!.changeCurrentState(FutureButtonState.initial);
      }
      // if (event.contains("https")) {
      //   images.add(event.replaceAll("\n", "").trim());
      //   setState(() {});
      // }
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
    _promptController.dispose();
    super.dispose();
  }

  bool isModelOn = false;

  late final Dio _dio = Dio();
  FutureButtonState _state = FutureButtonState.initial;

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
                      _buildLoraSelection(),
                      SizedBox(
                        height: 30,
                        child: Row(
                          children: [
                            Text(
                              'Input Prompt: ',
                              style: Styles.defaultButtonTextStyle,
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
                              style: Styles.defaultButtonTextStyle,
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
                          } else {
                            image = null;
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

                      SizedBox(
                        height: 30,
                        child: Consumer(
                          builder: (context, ref, child) {
                            final isOn = ref.watch(sdClientIsOnProvider);
                            return isOn.when(
                              data: (d) {
                                if (d) {
                                  _state = FutureButtonState.success;
                                }

                                return Row(
                                  children: [
                                    Text(
                                      "Model Status: ",
                                      style: Styles.defaultButtonTextStyle,
                                    ),
                                    const SizedBox(width: 10),
                                    if (!d && !isModelOn)
                                      Tooltip(
                                        message:
                                            "Model has not been initialized.",
                                        child: Icon(
                                          Icons.info_outline,
                                          size: 20,
                                          color: Colors.red,
                                        ),
                                      ),
                                    if (d || isModelOn)
                                      Tooltip(
                                        message: "Model is on.",
                                        child: Icon(
                                          Icons.on_device_training,
                                          size: 20,
                                          color: Colors.green,
                                        ),
                                      ),

                                    Spacer(),

                                    FutureStatusButton(
                                      onPressedAsync: () async {
                                        return await _dio.post(
                                          Api.sdInitial,
                                          data:
                                              SDInitializeRequest(
                                                enableImg2img: true,
                                              ).toJson(),
                                        );
                                      },
                                      initialState: _state,
                                      onDone: (v) {
                                        logger.d(v);
                                        if (v.data['status'] == "ok") {
                                          ToastUtils.success(
                                            context,
                                            title: "初始化成功",
                                          );
                                          setState(() {
                                            _state = FutureButtonState.success;
                                            isModelOn = true;
                                          });
                                        } else {
                                          ToastUtils.error(
                                            context,
                                            title: "初始化失败",
                                          );
                                          setState(() {
                                            _state = FutureButtonState.error;
                                          });
                                        }
                                      },
                                      initialChild: Text(
                                        "Init",
                                        style: Styles.defaultButtonTextStyle,
                                      ),
                                      errorChild: Text(
                                        "Retry",
                                        style: Styles.defaultButtonTextStyle,
                                      ),
                                      successChild: Text(
                                        "Re-init",
                                        style: Styles.defaultButtonTextStyle,
                                      ),
                                    ),
                                  ],
                                );
                              },
                              error:
                                  (error, stackTrace) => Container(
                                    height: 30,

                                    padding: EdgeInsets.all(5),
                                    child: Text(
                                      "Fetching model status error",
                                      style: Styles.defaultButtonTextStyleGrey,
                                    ),
                                  ),
                              loading:
                                  () => Container(
                                    height: 30,

                                    padding: EdgeInsets.all(5),
                                    child: Text(
                                      "Fetching model status...",
                                      style: Styles.defaultButtonTextStyleGrey,
                                    ),
                                  ),
                            );
                          },
                        ),
                      ),

                      _buildStrengthSlider(),

                      SizedBox(
                        height: 30,
                        child: Row(
                          children: [
                            Text(
                              "Generate Count: ",
                              style: Styles.defaultButtonTextStyle,
                            ),
                            const SizedBox(width: 10),
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
                                    [1, 2, 3, 4, 5, 10]
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

                            FutureStatusButtonSimple(
                              key: _buttonKey,
                              onPressed: () async {
                                if (_promptController.text.isEmpty) {
                                  return;
                                }

                                FileTypeResult? fileType =
                                    image == null
                                        ? null
                                        : FileType.fromBuffer(image!);
                                logger.d("file type: $fileType");
                                String? imgB64 =
                                    image == null ? null : base64Encode(image!);
                                if (imgB64 != null) {
                                  imgB64 =
                                      "data:${fileType?.mime};base64,$imgB64";
                                }

                                SDAugmentReq req = SDAugmentReq(
                                  strength: _strength,
                                  prompt: _promptController.text,
                                  jobType:
                                      imgB64 == null ? "txt2img" : "img2img",
                                  count: generateCount,
                                  img: imgB64,
                                  modelId: 1,
                                  loraName:
                                      selectedLora == "None"
                                          ? null
                                          : selectedLora.toLowerCase(),
                                );

                                logger.d(
                                  "enable prompt optimize: ${req.promptOptimize} and model id: ${req.modelId}, base64: ${imgB64?.length}",
                                );

                                sse(Api.sd, req.toJson(), ss);
                                _buttonKey.currentState!.changeCurrentState(
                                  FutureButtonState.loading,
                                );
                              },

                              initialChild: Text(
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
                              (v) => EditableImage(
                                onEdit: () {
                                  showGeneralDialog(
                                    barrierColor: Styles.barriarColor,
                                    barrierDismissible: true,
                                    barrierLabel: "DeepEditDialog",
                                    context: context,
                                    pageBuilder: (c, _, _) {
                                      return Center(
                                        child: DeepEditDialog(cvResp: v),
                                      );
                                    },
                                  );
                                },
                                width: 512,
                                height: 512,
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
            ),
          ],
        ),
      ),
    );
  }

  List<String> loraSelections = ["None", "PCB", "Leather"];
  late String selectedLora = loraSelections[0];

  Widget _buildLoraSelection() {
    return SizedBox(
      height: 30,
      child: Row(
        children: [
          Text("Lora selection:", style: Styles.defaultButtonTextStyle),
          const SizedBox(width: 10),
          SizedBox(
            width: 120,
            child: CustomDropDownButton<String>(
              buttonIcon:
                  ({required showedMenu}) => SizedBox(
                    height: 30,
                    // width: 30,
                    child: Center(
                      child: Icon(Icons.arrow_drop_down, color: Colors.black),
                    ),
                  ),
              buttonIconFirst: false,
              buttonStyle: ButtonStyle(
                fixedSize: WidgetStateProperty.all(Size(100, 20)),
                backgroundColor: WidgetStatePropertyAll(Colors.grey[300]),
                padding: WidgetStatePropertyAll(
                  const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
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
              buttonText: selectedLora.toString(),
              position: DropDownButtonPosition.bottomCenter,
              buttonIconColor: Colors.black,
              buttonTextStyle: Styles.defaultButtonTextStyle,
              menuItems:
                  loraSelections
                      .map(
                        (e) => CustomDropDownButtonItem(
                          value: e,
                          text: e.toString(),
                          onPressed: () {
                            if (e != selectedLora) {
                              setState(() {
                                selectedLora = e;
                              });
                              if (e == "None") {
                                _promptController.text = "";
                              } else if (e == "PCB") {
                                _promptController.text =
                                    "a photo of sks pcb contain 8 defects";
                              } else {
                                _promptController.text =
                                    "a macro photo of sks leather with a small dent and fine surface wrinkles";
                              }
                            }
                          },
                          buttonStyle: ButtonStyle(
                            fixedSize: WidgetStateProperty.all(Size(100, 20)),
                            backgroundColor: WidgetStatePropertyAll(
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
              selectedValue: selectedLora,
            ),
          ),
        ],
      ),
    );
  }

  double _strength = 0.3;
  Widget _buildStrengthSlider() {
    return SizedBox(
      height: 30,
      child: Row(
        children: [
          Text("Strength:", style: Styles.defaultButtonTextStyle),
          SizedBox(width: 10),
          Tooltip(
            message:
                "Noise strength, not work when image is not null. Larger values mean generation will be more different.",
            child: Icon(Icons.info, size: 20),
          ),

          const SizedBox(width: 30),
          SizedBox(
            width: 150,
            child: CupertinoSlider(
              value: _strength,
              min: 0.01,
              max: 0.99,
              divisions: 98,
              // label: _strength.toString(),
              onChanged: (double value) {
                setState(() {
                  _strength = value;
                });
              },
            ),
          ),
          const SizedBox(width: 10),
          Text(
            _strength.toStringAsFixed(2),
            style: Styles.defaultButtonTextStyleGrey,
          ),
        ],
      ),
    );
  }
}
