import 'package:auto_ml/utils/logger.dart';
import 'package:auto_ml/utils/styles.dart';
import 'package:flutter/material.dart';

Widget buildNodeDialogWidget({
  required BuildContext context,
  required String nodeName,
  required Widget Function(BuildContext) dialogWidgetBuilder,
  String barrierLabel = "node dialog",
  dynamic logBeforeDialog,
  dynamic logAfterDialog,
}) {
  return GestureDetector(
    onDoubleTap: () async {
      if (logBeforeDialog != null) {
        logger.i(logBeforeDialog);
      }

      await showGeneralDialog(
        barrierColor: Colors.transparent,
        transitionDuration: const Duration(milliseconds: 300),
        barrierDismissible: true,
        barrierLabel: barrierLabel,
        context: context,
        pageBuilder: (
          BuildContext context,
          Animation<double> animation,
          Animation<double> secondaryAnimation,
        ) {
          return Align(
            alignment: Alignment.centerRight,
            child: Padding(
              padding: EdgeInsets.only(
                right: MediaQuery.of(context).size.width * 0.1 + 20,
              ),
              child: dialogWidgetBuilder(context),
            ),
          );
        },
      );

      if (logAfterDialog != null) {
        logger.i(logAfterDialog);
      }
    },
    child: Container(
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(4),
        color: Colors.white,
      ),
      child: Center(
        child: Text(nodeName, style: Styles.defaultButtonTextStyleNormal),
      ),
    ),
  );
}
