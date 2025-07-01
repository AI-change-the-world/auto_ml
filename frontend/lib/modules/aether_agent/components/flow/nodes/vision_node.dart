import 'package:auto_ml/common/dialog_wrapper.dart';
import 'package:auto_ml/modules/aether_agent/components/flow/models/enums.dart';
import 'package:auto_ml/modules/aether_agent/components/flow/nodes/basic_config_widget.dart';
import 'package:auto_ml/modules/aether_agent/components/flow/nodes/node_dialog_widget.dart';
import 'package:auto_ml/modules/aether_agent/components/flow/notifiers/notifier.dart';
import 'package:auto_ml/modules/tool_models/models/tool_model_response.dart';
import 'package:auto_ml/modules/tool_models/notifier/model_notifier.dart';
import 'package:auto_ml/utils/logger.dart';
import 'package:auto_ml/utils/styles.dart';
import 'package:basic_dropdown_button/basic_dropwon_button_widget.dart';
import 'package:basic_dropdown_button/custom_dropdown_button.dart';
import 'package:flow_compose/flow_compose.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class VisionNodeWidget extends StatelessWidget {
  const VisionNodeWidget({super.key, required this.node});
  final NodeModel node;

  @override
  Widget build(BuildContext context) {
    return buildNodeDialogWidget(
      child: Container(
        padding: const EdgeInsets.all(10),
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(4),
          color: Colors.white,
        ),
        width: node.width,
        height: node.height,
        child: Center(child: Text(node.label)),
      ),
      context: context,
      dialogWidgetBuilder: (c) {
        // return _VisionNodeConfigWidet(data: node);
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
                  node.label,
                  style: Styles.defaultButtonTextStyle.copyWith(fontSize: 20),
                ),
                if (node.description != null)
                  Text(
                    node.description!,
                    style: Styles.defaultButtonTextStyleGrey,
                  ),
                SizedBox(height: 1),
                Expanded(
                  child: _VisionNodeConfigWidet(
                    data: node,
                    onDataChanged: (newData) {
                      node.data = newData;
                    },
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

class _VisionNodeConfigWidet extends BaseNodeConfigWidget {
  const _VisionNodeConfigWidet({
    required super.data,
    required super.onDataChanged,
  });

  @override
  ConsumerState<_VisionNodeConfigWidet> createState() =>
      __VisionNodeConfigWidetState();
}

class __VisionNodeConfigWidetState
    extends ConsumerState<_VisionNodeConfigWidet> {
  late Map<String, dynamic> thisData = Map.of(widget.data.data);

  late OutputDataType _outputDataType = getOutputDataTypeFromString(
    thisData["outputDataType"] ?? "",
  );

  // ignore: avoid_init_to_null
  late ToolModel? _toolModel = null;

  late final TextEditingController _promptController = TextEditingController();

  @override
  void dispose() {
    _promptController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    // final nodeInfo =
    //     ref.read(createFlowNotifier.notifier).boardController!.state.value.data;
    // logger.d("widget uuid  ${widget.uuid}");
    // for (final i in nodeInfo) {
    //   logger.d("${i.uuid}  ${i.type}  nodeInfo: ${i.prevData}");
    // }

    final nodeInfo = ref
        .read(createFlowNotifier.notifier)
        .boardController!
        .getNodeData(widget.data.uuid);

    logger.d("nodeInfo: ${nodeInfo?.prevData}");
    return Column(
      spacing: 10,
      children: [
        SizedBox(
          height: 30,
          child: Row(
            children: [
              Expanded(
                flex: 1,
                child: Text("Input key", style: Styles.defaultButtonTextStyle),
              ),
              // Expanded(
              //   flex: 1,
              //   child: Text(
              //     "Vision_out_${widget.uuid.split("-").first}",
              //     style: Styles.defaultButtonTextStyleGrey,
              //   ),
              // ),
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
                  "Select model",
                  style: Styles.defaultButtonTextStyle,
                ),
              ),

              Expanded(
                flex: 1,
                child: Consumer(
                  builder: (context, ref, _) {
                    // TODO 模型需要添加 det cls seg... 类型
                    final modelState = ref.watch(modelNotifierProvider);

                    return modelState.when(
                      data: (data) {
                        return CustomDropDownButton<ToolModel>(
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
                          buttonText:
                              _toolModel == null ? "null" : _toolModel!.name,
                          position: DropDownButtonPosition.bottomCenter,
                          buttonIconColor: Colors.black,
                          buttonTextStyle: Styles.defaultButtonTextStyle,
                          menuItems:
                              data.models
                                  .map(
                                    (e) => CustomDropDownButtonItem(
                                      value: e,
                                      text: "${e.name} #${e.type}",
                                      icon: Tooltip(
                                        message: e.description,
                                        child: Icon(Icons.info, size: 15),
                                      ),
                                      onPressed: () {
                                        if (e != _toolModel) {
                                          setState(() {
                                            _toolModel = e;
                                            if (_toolModel!.type == "mllm") {
                                              _outputDataType =
                                                  OutputDataType.text;
                                            } else if (_toolModel!.type ==
                                                "vision") {
                                              _outputDataType =
                                                  OutputDataType.PredictResults;
                                            } else if (_toolModel!.type ==
                                                "gd") {
                                              _outputDataType =
                                                  OutputDataType.PredictResults;
                                            }
                                            thisData['selectModel'] = e.name;
                                            thisData['outputDataType'] =
                                                _outputDataType.name;
                                          });
                                          widget.onDataChanged(thisData);
                                        }
                                      },
                                      buttonStyle: ButtonStyle(
                                        fixedSize: WidgetStateProperty.all(
                                          Size(200, 20),
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
                          selectedValue: _toolModel,
                        );
                      },
                      error: (error, stackTrace) => Text(error.toString()),
                      loading: () => Text("Loading"),
                    );
                  },
                ),
              ),
            ],
          ),
        ),
        if (_toolModel?.type == "gd" || _toolModel?.type == "mllm")
          SizedBox(
            height: 100,
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Expanded(
                  flex: 1,
                  child: Row(
                    children: [
                      Text(
                        "Input prompt",
                        style: Styles.defaultButtonTextStyle,
                      ),
                      SizedBox(width: 10),
                      if (_toolModel?.type == "gd")
                        Tooltip(
                          message: "GD prompt:\nperson;car;etc",
                          child: Icon(Icons.info, size: 15),
                        ),
                    ],
                  ),
                ),

                Expanded(
                  flex: 1,
                  // child: TextField(
                  //   maxLines: 4,
                  //   style: TextStyle(fontSize: 12, color: Colors.black),
                  //   decoration: InputDecoration(
                  //     hintStyle: TextStyle(fontSize: 12, color: Colors.grey),
                  //     contentPadding: EdgeInsets.only(
                  //       top: 10,
                  //       left: 10,
                  //       right: 10,
                  //     ),
                  //     border: OutlineInputBorder(),
                  //     focusedBorder: OutlineInputBorder(
                  //       borderSide: BorderSide(color: Colors.blueAccent),
                  //     ),
                  //     hintText: "Input prompt",
                  //   ),
                  // ),
                  child: Stack(
                    alignment: Alignment.bottomRight,
                    children: [
                      TextField(
                        controller: _promptController,
                        maxLines: 4,
                        style: TextStyle(fontSize: 12, color: Colors.black),
                        decoration: InputDecoration(
                          hintStyle: TextStyle(
                            fontSize: 12,
                            color: Colors.grey,
                          ),
                          contentPadding: EdgeInsets.fromLTRB(12, 12, 36, 12),
                          border: OutlineInputBorder(),
                          focusedBorder: OutlineInputBorder(
                            borderSide: BorderSide(color: Colors.blueAccent),
                          ),
                          hintText: "Input prompt",
                        ),
                      ),
                      Positioned(
                        right: 8,
                        bottom: 8,
                        child: MouseRegion(
                          cursor: SystemMouseCursors.click,
                          child: GestureDetector(
                            onTap: _showExpandedEditor,
                            child: Container(
                              padding: EdgeInsets.all(4),
                              decoration: BoxDecoration(
                                color: Colors.grey[300],
                                shape: BoxShape.circle,
                              ),
                              child: Icon(Icons.open_in_full, size: 18),
                            ),
                          ),
                        ),
                      ),
                    ],
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
                  "Output type",
                  style: Styles.defaultButtonTextStyle,
                ),
              ),
              Expanded(
                flex: 1,
                child: CustomDropDownButton<OutputDataType>(
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
                  buttonText: _outputDataType.name,
                  position: DropDownButtonPosition.bottomCenter,
                  buttonIconColor: Colors.black,
                  buttonTextStyle: Styles.defaultButtonTextStyle,
                  menuItems:
                      OutputDataType.values
                          .map(
                            (e) => CustomDropDownButtonItem(
                              value: e,
                              text: e.name,
                              icon: Tooltip(
                                message: e.description,
                                child: Icon(Icons.info, size: 15),
                              ),
                              onPressed: () {
                                if (e != _outputDataType) {
                                  setState(() {
                                    _outputDataType = e;
                                    thisData['outputDataType'] = e.name;
                                  });
                                  widget.onDataChanged(thisData);
                                }
                              },
                              buttonStyle: ButtonStyle(
                                fixedSize: WidgetStateProperty.all(
                                  Size(200, 20),
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
                  selectedValue: _outputDataType,
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
                child: Text("Output key", style: Styles.defaultButtonTextStyle),
              ),
              Expanded(
                flex: 1,
                child: Text(
                  "Vision_out_${widget.data.uuid.split("-").first}",
                  style: Styles.defaultButtonTextStyleGrey,
                ),
              ),
            ],
          ),
        ),

        SizedBox(
          height: 30,
          child: Row(
            children: [
              Expanded(flex: 1, child: SizedBox()),
              Expanded(
                flex: 1,
                child: ElevatedButton(
                  style: ElevatedButton.styleFrom(
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(4), // 设置圆角半径
                    ),
                    padding: EdgeInsets.symmetric(
                      horizontal: 6,
                      vertical: 3,
                    ), // 调整按钮大小
                  ),
                  onPressed: () {},
                  child: Text(
                    "Debug this step",
                    style: Styles.defaultButtonTextStyle,
                  ),
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }

  void _showExpandedEditor() async {
    final result = await showGeneralDialog<String>(
      context: context,
      barrierDismissible: true,
      barrierLabel: "input prompt",
      pageBuilder: (context, _, _) {
        TextEditingController dialogController = TextEditingController(
          text: _promptController.text,
        );
        return Center(
          child: dialogWrapper(
            width: 600,
            height: 400,
            child: Column(
              spacing: 10,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text("Prompt", style: Styles.defaultButtonTextStyle),
                Expanded(
                  child: TextField(
                    controller: dialogController,
                    maxLines: 15,
                    decoration: InputDecoration(border: OutlineInputBorder()),
                  ),
                ),
                SizedBox(
                  height: 30,
                  child: Row(
                    spacing: 20,
                    children: [
                      Spacer(),
                      ElevatedButton(
                        style: ElevatedButton.styleFrom(
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(4), // 设置圆角半径
                          ),
                          padding: EdgeInsets.symmetric(
                            horizontal: 6,
                            vertical: 3,
                          ), // 调整按钮大小
                        ),
                        onPressed: () => Navigator.pop(context),
                        child: Text(
                          "Cancel",
                          style: Styles.defaultButtonTextStyle,
                        ),
                      ),

                      ElevatedButton(
                        style: ElevatedButton.styleFrom(
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(4), // 设置圆角半径
                          ),
                          padding: EdgeInsets.symmetric(
                            horizontal: 6,
                            vertical: 3,
                          ), // 调整按钮大小
                        ),
                        onPressed:
                            () => Navigator.pop(context, dialogController.text),
                        child: Text(
                          "Confirm",
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

    if (result != null) {
      setState(() {
        _promptController.text = result;
      });
    }
  }
}
