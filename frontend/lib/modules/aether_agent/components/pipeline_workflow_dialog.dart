import 'dart:convert';

import 'package:auto_ml/common/dialog_wrapper.dart';
import 'package:flow_compose/flow_compose.dart';
import 'package:flutter/material.dart';

class PipelineWorkflowDialog extends StatefulWidget {
  const PipelineWorkflowDialog({super.key, required this.content});
  final String content;

  @override
  State<PipelineWorkflowDialog> createState() => _PipelineWorkflowDialogState();
}

class _PipelineWorkflowDialogState extends State<PipelineWorkflowDialog> {
  late final BoardController boardController;
  @override
  void initState() {
    super.initState();
    boardController = BoardController(
      initialState: BoardState(editable: false, data: [], edges: {}),
      nodes: [],
    );

    Map<String, dynamic> data = jsonDecode(widget.content);
    List<INode> nodes = [];
    List<Edge> edges = [];
    for (var node in data["nodes"]) {
      nodes.add(INode.fromJson(node));
    }
    for (var edge in data["edges"]) {
      edges.add(Edge.fromJson(edge));
    }

    boardController.reCreate(nodes, edges);
  }

  @override
  void dispose() {
    boardController.dispose();
    super.dispose();
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
