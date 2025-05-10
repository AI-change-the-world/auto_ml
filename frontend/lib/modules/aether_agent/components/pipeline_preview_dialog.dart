import 'package:auto_ml/common/dialog_wrapper.dart';
import 'package:auto_ml/utils/xml_utils.dart';
import 'package:flutter/material.dart';
import 'package:markdown_widget/markdown_widget.dart';

class PipelinePreviewDialog extends StatelessWidget {
  const PipelinePreviewDialog({super.key, required this.content});
  final String content;

  @override
  Widget build(BuildContext context) {
    return dialogWrapper(
      width: 400,
      height: 300,
      child: MarkdownWidget(data: "```xml\n${formatXml(content)}\n```"),
    );
  }
}
