import 'package:flutter/material.dart';

Widget dialogWrapper({
  required Widget child,
  double width = 300,
  double height = 300,
}) {
  return Material(
    elevation: 10,
    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10.0)),
    child: Container(
      padding: EdgeInsets.all(10),
      width: width,
      height: height,
      decoration: BoxDecoration(borderRadius: BorderRadius.circular(10.0)),
      child: child,
    ),
  );
}
