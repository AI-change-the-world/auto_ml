import 'package:auto_ml/modules/aether_agent/components/flow/nodes/start_node.dart';
import 'package:auto_ml/modules/aether_agent/components/flow/nodes/vision_node.dart';
import 'package:auto_ml/utils/logger.dart';
import 'package:flow_compose/flow_compose.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class CreateFlowNotifier extends Notifier {
  // ignore: avoid_init_to_null
  BoardController? boardController = null;

  @override
  build() {}

  void initController(BuildContext context) {
    boardController ??= BoardController(
      confirmBeforeDelete: true,
      style: BoardStyle(
        sidebarMaxHeight: MediaQuery.of(context).size.height * 0.8 * .95,
      ),
      initialState: BoardState(editable: true, data: [], edges: {}),
    );
    boardController!.nodeRenderRegistry["StartNode"] = (context, node) {
      return StartNodeWidget(node: node);
    };
    boardController!.setConfig(
      "StartNode",
      ExtraNodeConfig(width: 100, height: 40),
    );

    boardController!.nodeRenderRegistry["VisionNode"] = (context, node) {
      return VisionNodeWidget(node: node);
    };
    boardController!.setConfig(
      "VisionNode",
      ExtraNodeConfig(width: 120, height: 60),
    );

    boardController!.stream.listen((v) {
      logger.d("${v.$1.uuid}  ${v.$2.name}");
    });
  }
}

final createFlowNotifier = NotifierProvider<CreateFlowNotifier, void>(
  () => CreateFlowNotifier(),
);
