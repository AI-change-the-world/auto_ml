import 'dart:io';

import 'package:auto_ml/modules/label/models/annotation.dart';
import 'package:auto_ml/utils/logger.dart';

class LabelState {
  String current;
  String dataPath;
  String labelPath;
  String selectedAnnotationUuid;

  /// missing dataset type, such as yolo or sth else

  late List<MapEntry<String, String>> dataLabelPairs = [];

  List<Annotation> currentLabels;

  LabelState({
    this.current = "",
    required this.dataPath,
    required this.labelPath,
    this.currentLabels = const [],
    this.selectedAnnotationUuid = "",
  }) {
    _initializeDataLabelPairs();
  }

  LabelState copyWith({
    String? current,
    String? dataPath,
    String? labelPath,
    List<Annotation>? currentLabels,
    String? selectedAnnotationUuid,
  }) {
    return LabelState(
      current: current ?? this.current,
      dataPath: dataPath ?? this.dataPath,
      labelPath: labelPath ?? this.labelPath,
      currentLabels: currentLabels ?? this.currentLabels,
      selectedAnnotationUuid:
          selectedAnnotationUuid ?? this.selectedAnnotationUuid,
    );
  }

  void _initializeDataLabelPairs() {
    Directory dataDir = Directory(dataPath);
    Directory labelDir = Directory(labelPath);

    if (!dataDir.existsSync() || !labelDir.existsSync()) {
      logger.w('Error: One of the directories does not exist.');
      return;
    }

    // 读取所有文件，并构建 Map<文件名, 文件路径>
    Map<String, String> dataFiles = {
      for (var file in dataDir.listSync().whereType<File>())
        file.uri.pathSegments.last.split('.').first: file.path,
    };

    Map<String, String> labelFiles = {
      for (var file in labelDir.listSync().whereType<File>())
        file.uri.pathSegments.last.split('.').first: file.path,
    };

    // 生成 List<MapEntry<String, String>>
    dataLabelPairs = [
      for (var key in dataFiles.keys)
        if (labelFiles.containsKey(key))
          MapEntry(dataFiles[key]!, labelFiles[key]!),
    ];
  }
}
