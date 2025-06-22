import 'package:auto_ml/i18n/strings.g.dart';
import 'package:auto_ml/modules/dataset/constants.dart';
import 'package:auto_ml/modules/tool_models/components/try_widget.dart';
import 'package:auto_ml/modules/tool_models/models/new_tool_model_request.dart';
import 'package:auto_ml/modules/tool_models/notifier/model_dialog_notifier.dart';
import 'package:auto_ml/utils/styles.dart';
import 'package:basic_dropdown_button/basic_dropwon_button_widget.dart';
import 'package:basic_dropdown_button/custom_dropdown_button.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class NewModelDialog extends ConsumerStatefulWidget {
  const NewModelDialog({
    super.key,
    required this.initialType,
    this.modelName = "",
    this.s3Path = "",
    this.enabledMap = const {},
    this.description = "",
  });
  final ModelType initialType;
  final String s3Path;
  final String modelName;
  final String description;
  final Map<String, bool> enabledMap;

  @override
  ConsumerState<NewModelDialog> createState() => _NewModelDialogState();
}

class _NewModelDialogState extends ConsumerState<NewModelDialog> {
  late TextStyle titleStyle = TextStyle(
    fontSize: 16,
    fontWeight: FontWeight.bold,
  );

  late TextStyle labelStyle = TextStyle(
    fontSize: 12,
    fontWeight: FontWeight.bold,
  );

  late TextStyle textStyle = TextStyle(fontSize: 12);

  late TextStyle hintStyle = TextStyle(fontSize: 12, color: Colors.grey);
  late ModelType type = widget.initialType;

  final _nameController = TextEditingController();
  late final _descriptionController =
      TextEditingController()..text = widget.description;
  late final _modelNameController =
      TextEditingController()..text = widget.modelName;
  final _apiKeyController = TextEditingController();
  late final _baseUrlController = TextEditingController()..text = widget.s3Path;

  @override
  void dispose() {
    _nameController.dispose();
    _descriptionController.dispose();
    _modelNameController.dispose();
    _apiKeyController.dispose();
    _baseUrlController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(modelDialogNotifierProvider);
    return Material(
      borderRadius: BorderRadius.circular(4),
      elevation: 10,
      child: Container(
        padding: EdgeInsets.all(10),
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(4),
          color: Colors.white,
        ),
        width: state ? 600 : 400,
        height: type == ModelType.vision ? 370 : 430,
        child: Column(
          spacing: 10,
          children: [
            Row(
              children: [
                AnimatedContainer(
                  duration: Duration(milliseconds: 300),
                  width: state ? 300 : 380,
                  child: Column(
                    spacing: 10,
                    children: [
                      Row(
                        spacing: 10,
                        children: [
                          Expanded(
                            flex: 1,
                            child: Text(
                              t.dialogs.new_model.name,
                              style: labelStyle,
                            ),
                          ),
                          Expanded(
                            flex: 1,
                            child: Text(
                              t.dialogs.new_model.model_type,
                              style: labelStyle,
                            ),
                          ),
                        ],
                      ),
                      SizedBox(
                        height: 30,
                        child: Row(
                          spacing: 10,
                          children: [
                            Expanded(
                              flex: 1,
                              child: TextField(
                                controller: _nameController,
                                style: textStyle,
                                decoration: InputDecoration(
                                  hintStyle: hintStyle,
                                  contentPadding: EdgeInsets.only(
                                    top: 10,
                                    left: 10,
                                    right: 10,
                                  ),
                                  border: OutlineInputBorder(),
                                  focusedBorder: OutlineInputBorder(
                                    borderSide: BorderSide(
                                      color: Colors.blueAccent,
                                    ),
                                  ),
                                  hintText: "Name (required)",
                                ),
                              ),
                            ),

                            Expanded(
                              flex: 1,
                              child: CustomDropDownButton<ModelType>(
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
                                buttonText: type.name,
                                position: DropDownButtonPosition.bottomCenter,
                                buttonIconColor: Colors.black,
                                buttonTextStyle: TextStyle(color: Colors.black),
                                menuItems:
                                    widget.enabledMap['dropdown'] ?? true
                                        ? ModelType.values
                                            .map(
                                              (e) => CustomDropDownButtonItem(
                                                value: e,
                                                text: e.name,
                                                onPressed: () {
                                                  if (e != type) {
                                                    setState(() {
                                                      type = e;
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
                                                  textStyle:
                                                      WidgetStatePropertyAll(
                                                        const TextStyle(
                                                          color: Colors.black,
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
                                                ),
                                              ),
                                            )
                                            .toList()
                                        : [
                                          CustomDropDownButtonItem(
                                            value: ModelType.vision,
                                            text: ModelType.vision.name,
                                            onPressed: () {
                                              if (ModelType.vision != type) {
                                                setState(() {
                                                  type = ModelType.vision;
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
                                            ),
                                          ),
                                        ],
                                menuBorderRadius: BorderRadius.circular(8),
                                selectedValue: type,
                              ),
                            ),
                          ],
                        ),
                      ),

                      SizedBox(
                        child: Row(
                          children: [
                            Text(
                              type == ModelType.vision
                                  ? "Save path"
                                  : "Base Url",
                              style: labelStyle,
                            ),
                            SizedBox(width: 10),
                            if (type == ModelType.vision)
                              Tooltip(
                                message:
                                    "The path to save the model, usually a s3 file path",
                                child: Icon(
                                  Icons.info,
                                  size: 16,
                                  color: Colors.black,
                                ),
                              ),
                            Spacer(),
                          ],
                        ),
                      ),
                      SizedBox(
                        height: 30,
                        child: TextField(
                          controller: _baseUrlController,
                          enabled: widget.enabledMap["baseUrl"] ?? true,
                          style: textStyle,
                          decoration: InputDecoration(
                            hintStyle: hintStyle,
                            contentPadding: EdgeInsets.only(
                              top: 10,
                              left: 10,
                              right: 10,
                            ),
                            border: OutlineInputBorder(),
                            focusedBorder: OutlineInputBorder(
                              borderSide: BorderSide(color: Colors.blueAccent),
                            ),
                            hintText:
                                type == ModelType.vision
                                    ? "Save path"
                                    : "Base url",
                          ),
                        ),
                      ),
                      if (type != ModelType.vision)
                        SizedBox(
                          child: Row(
                            children: [
                              Text("Api Key", style: labelStyle),
                              Spacer(),
                            ],
                          ),
                        ),
                      if (type != ModelType.vision)
                        SizedBox(
                          height: 30,
                          child: TextField(
                            controller: _apiKeyController,
                            style: textStyle,
                            decoration: InputDecoration(
                              hintStyle: hintStyle,
                              contentPadding: EdgeInsets.only(
                                top: 10,
                                left: 10,
                                right: 10,
                              ),
                              border: OutlineInputBorder(),
                              focusedBorder: OutlineInputBorder(
                                borderSide: BorderSide(
                                  color: Colors.blueAccent,
                                ),
                              ),
                              hintText: "Api key",
                            ),
                          ),
                        ),
                      SizedBox(
                        child: Row(
                          children: [
                            Text(
                              t.dialogs.new_model.model_name,
                              style: labelStyle,
                            ),
                            Spacer(),
                          ],
                        ),
                      ),
                      SizedBox(
                        height: 30,
                        child: TextField(
                          enabled: widget.enabledMap["modelName"] ?? true,
                          controller: _modelNameController,
                          style: textStyle,
                          decoration: InputDecoration(
                            hintStyle: hintStyle,
                            contentPadding: EdgeInsets.only(
                              top: 10,
                              left: 10,
                              right: 10,
                            ),
                            border: OutlineInputBorder(),
                            focusedBorder: OutlineInputBorder(
                              borderSide: BorderSide(color: Colors.blueAccent),
                            ),
                            hintText: "Model Name",
                          ),
                        ),
                      ),

                      SizedBox(
                        child: Row(
                          children: [
                            Text(
                              t.dialogs.new_model.description,
                              style: labelStyle,
                            ),
                            Spacer(),
                          ],
                        ),
                      ),
                      TextField(
                        controller: _descriptionController,
                        style: textStyle,
                        maxLines: 4,
                        decoration: InputDecoration(
                          hintStyle: hintStyle,
                          contentPadding: EdgeInsets.only(
                            top: 10,
                            left: 10,
                            right: 10,
                          ),
                          border: OutlineInputBorder(),
                          focusedBorder: OutlineInputBorder(
                            borderSide: BorderSide(color: Colors.blueAccent),
                          ),
                          hintText: "Model Description",
                        ),
                      ),
                    ],
                  ),
                ),
                TryWidget(type: type),
              ],
            ),
            SizedBox(
              height: 30,
              child: Row(
                spacing: 10,
                children: [
                  Spacer(),
                  if (type != ModelType.vision)
                    ElevatedButton(
                      style: Styles.getDefaultButtonStyle(),
                      onPressed: () {
                        if (_modelNameController.text.isNotEmpty &&
                            _baseUrlController.text.isNotEmpty) {
                          ref
                              .read(modelDialogNotifierProvider.notifier)
                              .changeState();
                          Future.delayed(Duration(seconds: 1)).then((_) {
                            ref
                                .read(modelDialogNotifierProvider.notifier)
                                .tryModel(
                                  _modelNameController.text,
                                  _baseUrlController.text,
                                  type,
                                  apiKey: _apiKeyController.text,
                                );
                          });
                        }
                      },
                      child: Text("Try", style: Styles.defaultButtonTextStyle),
                    ),
                  ElevatedButton(
                    style: Styles.getDefaultButtonStyle(),
                    onPressed: () {
                      if (_nameController.text.isEmpty) {
                        return;
                      }

                      // Navigator.of(context).pop(dataset);
                      if (type == ModelType.vision) {
                        NewToolModelRequest request = NewToolModelRequest(
                          name: _nameController.text,
                          description: _descriptionController.text,
                          type: "vision",
                          baseUrl: _baseUrlController.text,
                          modelName: _modelNameController.text,
                        );
                        ref
                            .read(modelDialogNotifierProvider.notifier)
                            .newModel(request)
                            .then((_) {
                              // ignore: use_build_context_synchronously
                              Navigator.of(context).pop();
                            });
                      }
                    },
                    child: Text("Submit", style: Styles.defaultButtonTextStyle),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
