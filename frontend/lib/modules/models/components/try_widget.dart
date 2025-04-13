import 'package:auto_ml/modules/dataset/constants.dart';
import 'package:auto_ml/modules/models/notifier/model_dialog_notifier.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:gpt_markdown/gpt_markdown.dart';

class TryWidget extends ConsumerStatefulWidget {
  const TryWidget({super.key, required this.type});
  final ModelType type;

  @override
  ConsumerState<TryWidget> createState() => _TryWidgetState();
}

class _TryWidgetState extends ConsumerState<TryWidget> {
  String content = "";
  late Stream<String> stream =
      ref.read(modelDialogNotifierProvider.notifier).tryModelStream;

  @override
  void initState() {
    super.initState();
    content = "";
  }

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
                  return Container(
                    decoration: BoxDecoration(color: Colors.grey[200]),
                    height: 370,
                    child: SingleChildScrollView(
                      padding: EdgeInsets.all(10),
                      child: Column(
                        spacing: 10,
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          if (widget.type == ModelType.llm)
                            Align(
                              alignment: Alignment.centerRight,
                              child: Container(
                                padding: EdgeInsets.all(5),
                                decoration: BoxDecoration(
                                  color: Colors.white,
                                  borderRadius: BorderRadius.only(
                                    topLeft: Radius.circular(10),
                                    bottomLeft: Radius.circular(10),
                                    topRight: Radius.circular(10),
                                  ),
                                ),
                                child: GptMarkdown("hello"),
                              ),
                            ),
                          if (widget.type == ModelType.mllm)
                            Align(
                              alignment: Alignment.centerRight,
                              child: Container(
                                padding: EdgeInsets.all(5),
                                decoration: BoxDecoration(
                                  color: Colors.white,
                                  borderRadius: BorderRadius.only(
                                    topLeft: Radius.circular(10),
                                    bottomLeft: Radius.circular(10),
                                    topRight: Radius.circular(10),
                                  ),
                                ),
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    SizedBox(
                                      width: 50,
                                      height: 50,
                                      child: Image.asset("assets/test.png"),
                                    ),
                                    GptMarkdown("Describe this image"),
                                  ],
                                ),
                              ),
                            ),
                          Container(
                            padding: EdgeInsets.all(5),
                            decoration: BoxDecoration(
                              color: Colors.white,
                              borderRadius: BorderRadius.only(
                                topLeft: Radius.circular(10),
                                bottomRight: Radius.circular(10),
                                topRight: Radius.circular(10),
                              ),
                            ),
                            child: GptMarkdown(content),
                          ),
                        ],
                      ),
                    ),
                  );
                },
              )
              : null,
    );
  }
}
