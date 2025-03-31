import 'package:auto_ml/utils/styles.dart';
import 'package:flutter/material.dart';
import 'package:isar/isar.dart';

part 'dataset.g.dart';

enum DatasetType { image, video, audio, text, other }

extension DatasetExtension on DatasetType {
  Color get color {
    switch (this) {
      case DatasetType.image:
        return Styles.cardColors[0];
      case DatasetType.video:
        return Styles.cardColors[1];
      case DatasetType.audio:
        return Styles.cardColors[2];
      case DatasetType.text:
        return Styles.cardColors[3];
      case DatasetType.other:
        return Styles.cardColors[4];
    }
  }

  String get name =>
      {
        DatasetType.image: "Image",
        DatasetType.video: "Video",
        DatasetType.audio: "Audio",
        DatasetType.text: "Text",
        DatasetType.other: "Other",
      }[this]!;

  Icon icon({Color? color, double? size}) {
    switch (this) {
      case DatasetType.image:
        return Icon(Icons.image, color: color ?? Colors.white, size: size);
      case DatasetType.video:
        return Icon(
          Icons.video_collection,
          color: color ?? Colors.white,
          size: size,
        );
      case DatasetType.audio:
        return Icon(Icons.audiotrack, color: color ?? Colors.white, size: size);
      case DatasetType.text:
        return Icon(
          Icons.text_snippet,
          color: color ?? Colors.white,
          size: size,
        );
      case DatasetType.other:
        return Icon(Icons.extension, color: color ?? Colors.white, size: size);
    }
  }
}

enum DatasetTask { classification, segmentation, detection, other }

extension DatasetTaskExtension on DatasetTask {
  String get name =>
      {
        DatasetTask.classification: "Classification",
        DatasetTask.segmentation: "Segmentation",
        DatasetTask.detection: "Detection",
        DatasetTask.other: "Other",
      }[this]!;

  Icon icon({Color? color, double? size}) {
    switch (this) {
      case DatasetTask.classification:
        return Icon(Icons.class_, color: color ?? Colors.white, size: size);
      case DatasetTask.segmentation:
        return Icon(Icons.segment, color: color ?? Colors.white, size: size);
      case DatasetTask.detection:
        return Icon(Icons.search, color: color ?? Colors.white, size: size);
      default:
        return Icon(Icons.extension, color: color ?? Colors.white, size: size);
    }
  }
}

@collection
class Dataset {
  Id id = Isar.autoIncrement;

  @Index(unique: true)
  String? name;

  String? description;

  String? dataPath;

  @enumerated
  DatasetType type = DatasetType.image;

  @enumerated
  DatasetTask task = DatasetTask.classification;

  String? labelPath;

  int createAt = DateTime.now().millisecondsSinceEpoch;
}

/// 假数据
List<Dataset> fakeDataset() {
  return [
    Dataset()
      ..name = "Image"
      ..type = DatasetType.image
      ..dataPath = "data/image"
      ..labelPath = "data/image/label.txt",
    Dataset()
      ..name = "Video"
      ..type = DatasetType.video
      ..dataPath = "data/video"
      ..labelPath = "data/video/label.txt",
  ];
}
