import 'package:auto_ml/modules/models/notifier/model_dialog_notifier.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:markdown_widget/widget/markdown.dart';

class TryWidget extends ConsumerStatefulWidget {
  const TryWidget({super.key});

  @override
  ConsumerState<TryWidget> createState() => _TryWidgetState();
}

class _TryWidgetState extends ConsumerState<TryWidget> {
  String content = "";
  late Stream<String> stream =
      ref.read(modelDialogNotifierProvider.notifier).tryModelStream;

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(modelDialogNotifierProvider);
    WidgetsBinding.instance.addPostFrameCallback((_) {
      content = "";
    });

    return AnimatedContainer(
      margin: EdgeInsets.only(left: state ? 10 : 0),
      duration: Duration(milliseconds: 300),
      width: state ? 270 : 0,
      child:
          state
              ? StreamBuilder(
                stream: stream,
                builder: (c, s) {
                  if (s.hasData) {
                    content = content + (s.data as String);
                  }
                  return SizedBox(
                    height: 350,
                    child: MarkdownWidget(data: content),
                  );
                },
              )
              : null,
    );
  }
}
