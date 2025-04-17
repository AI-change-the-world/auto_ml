import 'package:auto_ml/utils/styles.dart';
import 'package:flutter/material.dart';

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

DatasetTask datasetTaskGetById(int id) {
  switch (id) {
    case 1:
      return DatasetTask.classification;
    case 2:
      return DatasetTask.detection;
    case 3:
      return DatasetTask.segmentation;
    default:
      return DatasetTask.other;
  }
}

enum DatasetFrom { local, s3, webdav, others }

extension DatasetFromExtension on DatasetFrom {
  String get name {
    switch (this) {
      case DatasetFrom.local:
        return 'Local';
      case DatasetFrom.s3:
        return 'S3';
      case DatasetFrom.webdav:
        return 'WebDAV';
      case DatasetFrom.others:
        return 'Others';
    }
  }

  int get index {
    switch (this) {
      case DatasetFrom.local:
        return 0;
      case DatasetFrom.s3:
        return 1;
      case DatasetFrom.webdav:
        return 2;
      case DatasetFrom.others:
        return 3;
    }
  }
}
