import 'package:flutter/material.dart';
import 'package:isar/isar.dart';

part 'model.g.dart';

enum ModelType { llm, mllm, vision }

extension ModelTypeExtension on ModelType {
  String get name {
    switch (this) {
      case ModelType.llm:
        return "LLM";
      case ModelType.mllm:
        return "MLLM";
      case ModelType.vision:
        return "Vision";
    }
  }

  Icon icon({Color? color, double? size}) {
    switch (this) {
      case ModelType.llm:
        return Icon(Icons.language, color: color, size: size);
      case ModelType.mllm:
        return Icon(Icons.image, color: color, size: size);
      case ModelType.vision:
        return Icon(Icons.view_stream, color: color, size: size);
    }
  }
}

@collection
class Model {
  Id id = Isar.autoIncrement;
  String? name;
  String? description;

  @enumerated
  ModelType modelType = ModelType.vision;

  int createAt = DateTime.now().millisecondsSinceEpoch;

  String? baseUrl;
  String? apiKey;
  String? modelName;
}
