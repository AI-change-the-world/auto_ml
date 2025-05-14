import 'package:auto_ml/common/dialog_wrapper.dart';
import 'package:auto_ml/utils/styles.dart';
import 'package:flutter/material.dart';

class ShortCutDialog extends StatefulWidget {
  const ShortCutDialog({super.key});

  @override
  State<ShortCutDialog> createState() => _ShortCutDialogState();
}

class _ShortCutDialogState extends State<ShortCutDialog> {
  @override
  Widget build(BuildContext context) {
    return dialogWrapper(
      width: 400,
      height: 300,
      child: Container(
        padding: EdgeInsets.all(10),
        child: Column(
          spacing: 10,
          children: [
            Row(
              children: [
                Text("Shortcuts", style: Styles.defaultButtonTextStyle),
                Spacer(),
              ],
            ),
            Row(
              spacing: 5,
              children: [
                Icon(Icons.keyboard),
                Text("W", style: Styles.defaultButtonTextStyle),
                Text(
                  "Switch to Add/Modify mode",
                  style: Styles.defaultButtonTextStyleGrey,
                ),
              ],
            ),
            Row(
              spacing: 5,
              children: [
                Icon(Icons.keyboard),
                Text("H", style: Styles.defaultButtonTextStyle),
                Text(
                  "Hide selected annotation",
                  style: Styles.defaultButtonTextStyleGrey,
                ),
              ],
            ),
            Row(
              spacing: 5,
              children: [
                Icon(Icons.keyboard),
                Text("D", style: Styles.defaultButtonTextStyle),
                Text(
                  "Delete selected annotation",
                  style: Styles.defaultButtonTextStyleGrey,
                ),
              ],
            ),
            Row(
              spacing: 5,
              children: [
                Icon(Icons.keyboard),
                Text("S", style: Styles.defaultButtonTextStyle),
                Text(
                  "Save annotations",
                  style: Styles.defaultButtonTextStyleGrey,
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
