import 'dart:io';
import 'dart:ui';

import 'package:auto_ml/modules/label/models/annotation.dart';

List<Annotation> parseYoloAnnotations(
  String filePath,
  double imageWidth,
  double imageHeight,
) {
  List<Annotation> annotations = [];
  File file = File(filePath);
  List<String> lines = file.readAsLinesSync();

  for (String line in lines) {
    List<String> parts = line.split(' ');
    if (parts.length != 5) continue; // 确保格式正确

    int id = int.parse(parts[0]);
    double xCenter = double.parse(parts[1]) * imageWidth;
    double yCenter = double.parse(parts[2]) * imageHeight;
    double width = double.parse(parts[3]) * imageWidth;
    double height = double.parse(parts[4]) * imageHeight;

    double xMin = xCenter - width / 2;
    double yMin = yCenter - height / 2;
    Offset position = Offset(xMin, yMin);

    annotations.add(Annotation(position, width, height, id));
  }

  return annotations;
}
