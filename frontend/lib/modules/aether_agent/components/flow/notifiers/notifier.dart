import 'package:auto_ml/modules/aether_agent/components/flow/nodes/start_node.dart';
import 'package:auto_ml/modules/aether_agent/components/flow/nodes/vision_node.dart';
import 'package:auto_ml/utils/logger.dart';
import 'package:flow_compose/flow_compose.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class CreateFlowNotifier extends AutoDisposeNotifier {
  // ignore: avoid_init_to_null
  BoardController? boardController = null;

  @override
  build() {}

  void initController(BuildContext context) {
    boardController ??= BoardController(
      confirmBeforeDelete: true,
      style: BoardStyle(
        sidebarMaxHeight: MediaQuery.of(context).size.height * 0.8 * 0.875,
      ),
      initialState: BoardState(editable: true, data: [], edges: {}),
      nodes: [
        StartNode(label: '开始', uuid: 'start', offset: Offset.zero),
        VisionNode(label: "视觉", uuid: 'vision', offset: Offset.zero),
      ],
    );

    boardController!.stream.listen((v) {
      logger.d("${v.$1.uuid}  ${v.$2.name}");
    });
  }
}

final createFlowNotifier =
    AutoDisposeNotifierProvider<CreateFlowNotifier, void>(
      () => CreateFlowNotifier(),
    );
