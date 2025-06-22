import 'package:auto_ml/utils/logger.dart';
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
      return GestureDetector(
        onDoubleTap: () async {
          logger.i(prevData);
          await showGeneralDialog(
            barrierColor: Colors.transparent,
            transitionDuration: const Duration(milliseconds: 300),
            barrierDismissible: true,
            barrierLabel: "vision node dialog",
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
            Expanded(child: Container()),
          ],
        ),
      ),
    );
  }
}
