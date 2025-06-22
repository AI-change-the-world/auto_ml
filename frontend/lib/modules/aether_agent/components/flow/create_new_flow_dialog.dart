import 'package:auto_ml/common/dialog_wrapper.dart';
import 'package:auto_ml/modules/aether_agent/components/flow/nodes/start_node.dart';
import 'package:auto_ml/modules/aether_agent/components/flow/nodes/vision_node.dart';
import 'package:flow_compose/flow_compose.dart';
import 'package:flutter/material.dart';

class CreateNewFlowDialog extends StatefulWidget {
  const CreateNewFlowDialog({super.key});

  @override
  State<CreateNewFlowDialog> createState() => _CreateNewFlowDialogState();
}

class _CreateNewFlowDialogState extends State<CreateNewFlowDialog> {
  late final BoardController boardController;

  @override
  void initState() {
    super.initState();
    boardController = BoardController(
      confirmBeforeDelete: true,
      initialState: BoardState(editable: true, data: [], edges: {}),
      nodes: [
        StartNode(label: '开始', uuid: 'start', offset: Offset.zero),
        VisionNode(label: "视觉", uuid: 'vision', offset: Offset.zero),
      ],
    );
  }

  @override
  Widget build(BuildContext context) {
    return dialogWrapper(
      width: MediaQuery.of(context).size.width * 0.8,
      height: MediaQuery.of(context).size.height * 0.8,
      child: InfiniteDrawingBoard(controller: boardController),
    );
  }
}
