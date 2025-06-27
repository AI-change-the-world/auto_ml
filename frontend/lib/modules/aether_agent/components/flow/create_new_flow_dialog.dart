import 'package:auto_ml/common/dialog_wrapper.dart';
import 'package:auto_ml/modules/aether_agent/components/flow/notifiers/notifier.dart';
import 'package:flow_compose/flow_compose.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class CreateNewFlowDialog extends ConsumerStatefulWidget {
  const CreateNewFlowDialog({super.key});

  @override
  ConsumerState<CreateNewFlowDialog> createState() =>
      _CreateNewFlowDialogState();
}

class _CreateNewFlowDialogState extends ConsumerState<CreateNewFlowDialog> {
  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    ref.read(createFlowNotifier.notifier).initController(context);
  }

  @override
  Widget build(BuildContext context) {
    return dialogWrapper(
      width: MediaQuery.of(context).size.width * 0.8,
      height: MediaQuery.of(context).size.height * 0.8,
      child: InfiniteDrawingBoard(
        controller: ref.read(createFlowNotifier.notifier).boardController!,
      ),
    );
  }
}
