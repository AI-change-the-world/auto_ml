import 'package:auto_ml/modules/aether_agent/components/flow/models/enums.dart';
import 'package:auto_ml/utils/logger.dart';
import 'package:auto_ml/utils/styles.dart';
import 'package:basic_dropdown_button/basic_dropwon_button_widget.dart';
import 'package:basic_dropdown_button/custom_dropdown_button.dart';
import 'package:flow_compose/flow_compose.dart';
import 'package:flutter/material.dart';
import 'package:toggle_switch/toggle_switch.dart';

class StartNode extends INode {
  StartNode({
    required super.label,
    required super.uuid,
    required super.offset,
    super.width = 100,
    super.height = 50,
    super.nodeName = "开始",
    super.description = "设置输入参数的相关信息，用于流程的开始",
    super.builderName = "StartNode",
  }) {
    builder = (context) {
      return GestureDetector(
        onDoubleTap: () async {
          await showGeneralDialog(
            barrierColor: Colors.transparent,
            transitionDuration: const Duration(milliseconds: 300),
            barrierDismissible: true,
            barrierLabel: "start node dialog",
            context: context,
            pageBuilder: (
              BuildContext context,
              Animation<double> animation,
              Animation<double> secondaryAnimation,
            ) {
              return Align(
                alignment: Alignment.centerRight,
                child: Padding(
                  padding: EdgeInsetsGeometry.only(
                    right: MediaQuery.of(context).size.width * 0.1 + 20,
                  ),
                  child: dialogWidget(context),
                ),
              );
            },
          );
          logger.i(data);
        },
        child: Container(
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(4),
            color: Colors.white,
          ),
          child: Center(
            child: Text(nodeName, style: Styles.defaultButtonTextStyleNormal),
          ),
        ),
      );
    };
  }

  factory StartNode.fromJson(Map<String, dynamic> json) {
    String uuid = json["uuid"] ?? "";
    String label = json["label"] ?? "";
    Offset offset = Offset(json["offset"]["dx"], json["offset"]["dy"]);
    double width = json["width"] ?? 300;
    double height = json["height"] ?? 400;
    String nodeName = json["nodeName"] ?? "base";
    String description =
        json["description"] ?? "Base node, just for testing purposes";
    String builderName = json["builderName"] ?? "base";
    // Map<String, dynamic>? data = json["data"];

    return StartNode(
      offset: offset,
      width: width,
      height: height,
      nodeName: nodeName,
      description: description,
      builderName: builderName,
      label: label,
      uuid: uuid,
    );
  }

  @override
  INode copyWith({
    double? width,
    double? height,
    String? label,
    String? uuid,
    Offset? offset,
    List<INode>? children,
    Map<String, dynamic>? data,
  }) {
    return StartNode(
      width: width ?? this.width,
      height: height ?? this.height,
      label: label ?? this.label,
      uuid: uuid ?? this.uuid,
      offset: offset ?? this.offset,
    );
  }
}

extension StartNodeExtension on StartNode {
  Widget dialogWidget(BuildContext context) {
    return Material(
      elevation: 10,
      borderRadius: BorderRadius.circular(20),
      child: Container(
        padding: EdgeInsets.all(20),
        width: 300,
        height: MediaQuery.of(context).size.height * 0.7,
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(20),
        ),
        child: Column(
          spacing: 10,
          children: [
            Text(
              nodeName,
              style: Styles.defaultButtonTextStyle.copyWith(fontSize: 20),
            ),
            Text(description, style: Styles.defaultButtonTextStyleGrey),
            SizedBox(height: 1),
            Expanded(
              child: _StartNodeConfigWidget(
                data: data,
                onChanged: (d) {
                  data = d;
                },
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// ignore: must_be_immutable
class _StartNodeConfigWidget extends StatefulWidget {
  _StartNodeConfigWidget({required this.data, required this.onChanged});
  Map<String, dynamic>? data;
  final void Function(Map<String, dynamic> newData) onChanged;

  @override
  State<_StartNodeConfigWidget> createState() => __StartNodeConfigWidgetState();
}

class __StartNodeConfigWidgetState extends State<_StartNodeConfigWidget> {
  late Map<String, dynamic> thisData =
      widget.data ??
      {
        "inputDataType": InputDataType.text.name,
        "inputSourceType": InputSourceType.s3.name,
        "isList": false,
      };
  late InputDataType _inputDataType =
      thisData['inputDataType'] == null
          ? InputDataType.text
          : getDataTypeFromString(thisData['inputDataType'] as String);

  late InputSourceType _inputSourceType =
      thisData['inputSourceType'] == null
          ? InputSourceType.s3
          : getSourceTypeFromString(thisData['inputSourceType'] as String);

  late bool isList =
      thisData['isList'] == null ? false : thisData['isList'] as bool;

  late final TextEditingController _textEditingController =
      TextEditingController()..text = thisData['inputName'] ?? "";

  @override
  void dispose() {
    _textEditingController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      spacing: 10,
      children: [
        SizedBox(
          height: 30,
          child: Row(
            children: [
              Expanded(
                flex: 1,
                child: Text("Data Type", style: Styles.defaultButtonTextStyle),
              ),
              Expanded(
                flex: 1,
                child: CustomDropDownButton<InputDataType>(
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
                  buttonText: _inputDataType.name,
                  position: DropDownButtonPosition.bottomCenter,
                  buttonIconColor: Colors.black,
                  buttonTextStyle: Styles.defaultButtonTextStyle,
                  menuItems:
                      InputDataType.values
                          .map(
                            (e) => CustomDropDownButtonItem(
                              value: e,
                              text: e.name,
                              onPressed: () {
                                if (e != _inputDataType) {
                                  setState(() {
                                    _inputDataType = e;
                                    thisData['inputDataType'] = e.name;
                                  });
                                  widget.onChanged(thisData);
                                }
                              },
                              buttonStyle: ButtonStyle(
                                fixedSize: WidgetStateProperty.all(
                                  Size(100, 20),
                                ),
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
                  selectedValue: _inputDataType,
                ),
              ),
            ],
          ),
        ),
        SizedBox(
          height: 30,
          child: Row(
            children: [
              Expanded(
                flex: 1,
                child: Text(
                  "Data Source",
                  style: Styles.defaultButtonTextStyle,
                ),
              ),
              Expanded(
                flex: 1,
                child: CustomDropDownButton<InputSourceType>(
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
                  buttonText: _inputSourceType.name,
                  position: DropDownButtonPosition.bottomCenter,
                  buttonIconColor: Colors.black,
                  buttonTextStyle: Styles.defaultButtonTextStyle,
                  menuItems:
                      InputSourceType.values
                          .map(
                            (e) => CustomDropDownButtonItem(
                              value: e,
                              text: e.name,
                              onPressed: () {
                                if (e != _inputSourceType) {
                                  setState(() {
                                    _inputSourceType = e;
                                    thisData['inputSourceType'] = e.name;
                                  });
                                  widget.onChanged(thisData);
                                }
                              },
                              buttonStyle: ButtonStyle(
                                fixedSize: WidgetStateProperty.all(
                                  Size(100, 20),
                                ),
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
                  selectedValue: _inputSourceType,
                ),
              ),
            ],
          ),
        ),

        SizedBox(
          height: 30,
          child: Row(
            children: [
              Expanded(
                flex: 1,
                child: Text("Is List", style: Styles.defaultButtonTextStyle),
              ),
              Expanded(
                flex: 1,
                child: ToggleSwitch(
                  minWidth: 65.0,
                  initialLabelIndex: isList ? 0 : 1,
                  cornerRadius: 20.0,
                  activeBgColors: [
                    [Colors.cyan],
                    [Colors.redAccent],
                  ],
                  activeFgColor: Colors.white,
                  inactiveBgColor: Colors.grey,
                  inactiveFgColor: Colors.white,
                  totalSwitches: 2,
                  labels: ['YES', 'NO'],
                  icons: [null, null],
                  customWidgets: [
                    Text(
                      "Yes",
                      style: Styles.defaultButtonTextStyle.copyWith(
                        color: Colors.white,
                      ),
                    ),
                    Text(
                      "No",
                      style: Styles.defaultButtonTextStyle.copyWith(
                        color: Colors.white,
                      ),
                    ),
                  ],
                  fontSize: 12,
                  onToggle: (index) {
                    setState(() {
                      isList = index == 0;
                      thisData['isList'] = isList;
                    });
                    widget.onChanged(thisData);
                  },
                ),
              ),
            ],
          ),
        ),

        SizedBox(
          height: 30,
          child: Row(
            children: [
              Expanded(
                flex: 1,
                child: Text("Input name", style: Styles.defaultButtonTextStyle),
              ),
              Expanded(
                flex: 1,
                child: TextField(
                  onChanged: (value) {
                    thisData['inputName'] = value;
                    widget.onChanged(thisData);
                  },
                  controller: _textEditingController,
                  style: TextStyle(fontSize: 12, color: Colors.black),
                  decoration: InputDecoration(
                    hintStyle: TextStyle(fontSize: 12, color: Colors.grey),
                    contentPadding: EdgeInsets.only(
                      top: 10,
                      left: 10,
                      right: 10,
                    ),
                    border: OutlineInputBorder(),
                    focusedBorder: OutlineInputBorder(
                      borderSide: BorderSide(color: Colors.blueAccent),
                    ),
                    hintText: "If empty, will use default name",
                  ),
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}
