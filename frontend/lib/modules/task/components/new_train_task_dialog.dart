import 'package:auto_ml/common/dialog_wrapper.dart';
import 'package:auto_ml/modules/dataset/constants.dart';
import 'package:auto_ml/modules/task/models/base_model_response.dart';
import 'package:auto_ml/modules/task/notifier/new_train_task_notifier.dart';
import 'package:auto_ml/utils/styles.dart';
import 'package:basic_dropdown_button/basic_dropwon_button_widget.dart';
import 'package:basic_dropdown_button/custom_dropdown_button.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class NewTrainTaskDialog extends StatefulWidget {
  const NewTrainTaskDialog({super.key, required this.typeId});
  final int typeId;

  @override
  State<NewTrainTaskDialog> createState() => _NewTrainTaskDialogState();
}

/*
epochs=2,
imgsz=640,
batch=5,
*/

class _NewTrainTaskDialogState extends State<NewTrainTaskDialog> {
  // ignore: avoid_init_to_null
  late BaseModel? selectedModel = null;

  late TextEditingController epochsController =
      TextEditingController()..text = "5";
  late TextEditingController imgszController =
      TextEditingController()..text = "640";
  late TextEditingController batchController =
      TextEditingController()..text = "5";

  @override
  void dispose() {
    epochsController.dispose();
    imgszController.dispose();
    batchController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Consumer(
      builder: (c, ref, _) {
        final state = ref.watch(baseModelsProvider(widget.typeId));

        return dialogWrapper(
          width: 300,
          height: 270,
          child: Container(
            padding: EdgeInsets.all(10),

            child: Column(
              spacing: 10,
              children: [
                Text(
                  "Train Task (${datasetTaskGetById(widget.typeId).name})",
                  style: Styles.titleStyle,
                ),
                SizedBox(
                  height: 30,
                  child: Row(
                    spacing: 10,
                    children: [
                      Expanded(
                        flex: 1,
                        child: Text(
                          "Select base model",
                          style: Styles.defaultButtonTextStyle,
                        ),
                      ),
                      Expanded(
                        flex: 1,
                        child: state.when(
                          data: (data) {
                            selectedModel ??= data.first;
                            return CustomDropDownButton<BaseModel>(
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
                              buttonText: selectedModel?.name,
                              position: DropDownButtonPosition.bottomCenter,
                              buttonIconColor: Colors.black,
                              buttonTextStyle: TextStyle(color: Colors.black),
                              menuItems:
                                  data
                                      .map(
                                        (e) => CustomDropDownButtonItem(
                                          value: e,
                                          text: e.name,
                                          onPressed: () {
                                            if (e != selectedModel) {
                                              setState(() {
                                                selectedModel = e;
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
                              selectedValue: selectedModel,
                            );
                          },
                          error:
                              (e, _) => Text(
                                e.toString(),
                                style: TextStyle(
                                  color: Colors.red,
                                  fontSize: 12,
                                ),
                              ),
                          loading: () => CircularProgressIndicator(),
                        ),
                      ),
                    ],
                  ),
                ),
                // epoch
                SizedBox(
                  height: 30,
                  child: Row(
                    spacing: 10,
                    children: [
                      Expanded(
                        flex: 1,
                        child: Text(
                          "Epoch",
                          style: Styles.defaultButtonTextStyle,
                        ),
                      ),
                      Expanded(
                        flex: 1,
                        child: TextField(
                          controller: epochsController,
                          // controller: _nameController,
                          style: Styles.defaultButtonTextStyleNormal,
                          decoration: InputDecoration(
                            hintStyle: Styles.hintStyle,
                            contentPadding: EdgeInsets.only(
                              top: 10,
                              left: 10,
                              right: 10,
                            ),
                            border: OutlineInputBorder(),
                            focusedBorder: OutlineInputBorder(
                              borderSide: BorderSide(color: Colors.blueAccent),
                            ),
                            hintText: "epochs, default 5",
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
                // image size
                SizedBox(
                  height: 30,
                  child: Row(
                    spacing: 10,
                    children: [
                      Expanded(
                        flex: 1,
                        child: Text(
                          "Image size",
                          style: Styles.defaultButtonTextStyle,
                        ),
                      ),
                      Expanded(
                        flex: 1,
                        child: TextField(
                          controller: imgszController,
                          // controller: _nameController,
                          style: Styles.defaultButtonTextStyleNormal,
                          decoration: InputDecoration(
                            hintStyle: Styles.hintStyle,
                            contentPadding: EdgeInsets.only(
                              top: 10,
                              left: 10,
                              right: 10,
                            ),
                            border: OutlineInputBorder(),
                            focusedBorder: OutlineInputBorder(
                              borderSide: BorderSide(color: Colors.blueAccent),
                            ),
                            hintText: "Image size, default 640",
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
                // batch
                SizedBox(
                  height: 30,
                  child: Row(
                    spacing: 10,
                    children: [
                      Expanded(
                        flex: 1,
                        child: Text(
                          "Batch",
                          style: Styles.defaultButtonTextStyle,
                        ),
                      ),
                      Expanded(
                        flex: 1,
                        child: TextField(
                          controller: batchController,
                          // controller: _nameController,
                          style: Styles.defaultButtonTextStyleNormal,
                          decoration: InputDecoration(
                            hintStyle: Styles.hintStyle,
                            contentPadding: EdgeInsets.only(
                              top: 10,
                              left: 10,
                              right: 10,
                            ),
                            border: OutlineInputBorder(),
                            focusedBorder: OutlineInputBorder(
                              borderSide: BorderSide(color: Colors.blueAccent),
                            ),
                            hintText: "batch size, default 5",
                          ),
                        ),
                      ),
                    ],
                  ),
                ),

                SizedBox(
                  height: 30,
                  child: Row(
                    children: [
                      Spacer(),
                      ElevatedButton(
                        style: Styles.getDefaultStyle(),
                        onPressed: () {
                          Map<String, dynamic> data = {
                            "name": selectedModel?.name ?? "yolo11n.pt",
                            "epoch": int.tryParse(epochsController.text) ?? 5,
                            "batch": int.tryParse(batchController.text) ?? 5,
                            "size": int.tryParse(imgszController.text) ?? 640,
                          };

                          Navigator.of(context).pop(data);
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
        );
      },
    );
  }
}
