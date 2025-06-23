import 'package:auto_ml/modules/aether_agent/components/flow/nodes/basic_config_widget.dart';
import 'package:auto_ml/modules/aether_agent/components/flow/nodes/node_dialog_widget.dart';
import 'package:auto_ml/utils/styles.dart';
import 'package:flow_compose/flow_compose.dart';
import 'package:flutter/material.dart';

class VisionNode extends INode {
  VisionNode({
    required super.label,
    required super.uuid,
    required super.offset,
    super.width = 125,
    super.height = 60,
    super.nodeName = "视觉模型节点",
    super.description = "设置视觉节点的相关参数，输入必须是图片、视频数据（或者图片、视频的列表数据）",
    super.builderName = "VisionNode",
  }) {
    builder = (context) {
      return buildNodeDialogWidget(
        context: context,
        nodeName: nodeName,
        dialogWidgetBuilder: dialogWidget,
        barrierLabel: "vision node dialog",
        logBeforeDialog: prevData,
        logAfterDialog: data,
      );
    };
  }

  factory VisionNode.fromJson(Map<String, dynamic> json) {
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

    return VisionNode(
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
    return VisionNode(
      width: width ?? this.width,
      height: height ?? this.height,
      label: label ?? this.label,
      uuid: uuid ?? this.uuid,
      offset: offset ?? this.offset,
    );
  }
}

extension StartNodeExtension on VisionNode {
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
              child: _VisionNodeConfigWidet(
                data: data,
                onChanged: (data) {
                  this.data = data;
                },
                uuid: uuid,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _VisionNodeConfigWidet extends BaseNodeConfigWidget {
  const _VisionNodeConfigWidet({
    required super.data,
    required super.onChanged,
    required super.uuid,
  });

  @override
  State<_VisionNodeConfigWidet> createState() => __VisionNodeConfigWidetState();
}

class __VisionNodeConfigWidetState extends State<_VisionNodeConfigWidet> {
  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
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
                  "Vision_out_${widget.uuid.split("-").first}",
                  style: Styles.defaultButtonTextStyleGrey,
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}
