import 'package:flow_compose/flow_compose.dart';
import 'package:flutter/material.dart';

@Deprecated("弃用")
class BasicNode extends INode {
  BasicNode({
    required super.label,
    required super.uuid,
    required super.offset,
    super.width = 100,
    super.height = 50,
    super.nodeName = "开始",
    super.description = "启动节点，用于流程的开始",
    super.builderName = "StartNode",
  });

  factory BasicNode.fromJson(Map<String, dynamic> json) {
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

    return BasicNode(
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
}
