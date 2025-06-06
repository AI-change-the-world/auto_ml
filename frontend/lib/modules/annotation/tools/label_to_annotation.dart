import 'dart:math';
import 'dart:ui';

import 'package:auto_ml/modules/annotation/models/annotation.dart';

List<Annotation> parseYoloAnnotations(
  String fileContent,
  double imageWidth,
  double imageHeight,
) {
  List<Annotation> annotations = [];
  List<String> lines = fileContent.split('\n');

  for (String line in lines) {
    List<String> parts = line.trim().split(' ');
    if (parts.length < 5) continue; // 确保格式正确

    int id = int.parse(parts[0]);
    double xCenter = min(double.parse(parts[1]), 1) * imageWidth;
    double yCenter = min(double.parse(parts[2]), 1) * imageHeight;
    double width = min(double.parse(parts[3]), 1) * imageWidth;
    double height = min(double.parse(parts[4]), 1) * imageHeight;

    double xMin = xCenter - width / 2;
    double yMin = yCenter - height / 2;
    Offset position = Offset(xMin, yMin);

    annotations.add(Annotation(position, width, height, id));
  }

  return annotations;
}

List<Annotation> parseYoloAnnotationsWithClasses(
  String fileContent,
  double imageWidth,
  double imageHeight,
  List<String> classes,
) {
  List<Annotation> annotations = [];
  List<String> lines = fileContent.split('\n');

  for (String line in lines) {
    List<String> parts = line.trim().split(' ');
    if (parts.length < 5) continue; // 确保格式正确

    int id = classes.indexOf(parts[0]);
    double xCenter = min(double.parse(parts[1]), 1) * imageWidth;
    double yCenter = min(double.parse(parts[2]), 1) * imageHeight;
    double width = min(double.parse(parts[3]), 1) * imageWidth;
    double height = min(double.parse(parts[4]), 1) * imageHeight;

    double xMin = xCenter - width / 2;
    double yMin = yCenter - height / 2;
    Offset position = Offset(xMin, yMin);

    annotations.add(Annotation(position, width, height, id));
  }

  return annotations;
}

String toYoloAnnotations(
  List<Annotation> annotations,
  double imageWidth,
  double imageHeight,
) {
  final buffer = StringBuffer();

  for (final annotation in annotations) {
    final xCenter =
        (annotation.position.dx + annotation.width / 2) / imageWidth;
    final yCenter =
        (annotation.position.dy + annotation.height / 2) / imageHeight;
    final widthNorm = annotation.width / imageWidth;
    final heightNorm = annotation.height / imageHeight;

    buffer.writeln(
      '${annotation.id} ${xCenter.toStringAsFixed(6)} ${yCenter.toStringAsFixed(6)} ${widthNorm.toStringAsFixed(6)} ${heightNorm.toStringAsFixed(6)}',
    );
  }

  return buffer.toString();
}
