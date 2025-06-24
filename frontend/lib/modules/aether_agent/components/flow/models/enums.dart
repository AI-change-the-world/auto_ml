enum InputDataType { text, image, audio, video }

extension InputDataTypeExtension on InputDataType {
  String get name {
    switch (this) {
      case InputDataType.text:
        return 'text';
      case InputDataType.image:
        return 'image';
      case InputDataType.audio:
        return 'audio';
      case InputDataType.video:
        return 'video';
    }
  }
}

InputDataType getDataTypeFromString(String value) {
  switch (value) {
    case 'text':
      return InputDataType.text;
    case 'image':
      return InputDataType.image;
    case 'audio':
      return InputDataType.audio;
    case 'video':
      return InputDataType.video;
    default:
      return InputDataType.text;
  }
}

enum InputSourceType { s3, fileUpload }

extension InputSourceTypeExtension on InputSourceType {
  String get name {
    switch (this) {
      case InputSourceType.s3:
        return 's3';
      case InputSourceType.fileUpload:
        return 'fileUpload';
    }
  }
}

InputSourceType getSourceTypeFromString(String value) {
  switch (value) {
    case 's3':
      return InputSourceType.s3;
    case 'fileUpload':
      return InputSourceType.fileUpload;
    default:
      return InputSourceType.s3;
  }
}

// ignore: constant_identifier_names
enum OutputDataType { text, PredictResults, ClsPredictResults }

extension OutputDataTypeExtension on OutputDataType {
  String get name {
    switch (this) {
      case OutputDataType.text:
        return 'text';
      case OutputDataType.PredictResults:
        return 'PredictResults';
      case OutputDataType.ClsPredictResults:
        return 'ClsPredictResults';
    }
  }

  String get description {
    switch (this) {
      case OutputDataType.text:
        return 'text';
      case OutputDataType.PredictResults:
        return """
**PredictResults example:**

```json
{
  "image_id": "image_001.jpg",
  "results": [
    {
      "name": "person",
      "obj_class": 0,
      "confidence": 0.95,
      "box": {
        "x1": 100.0,
        "y1": 150.0,
        "x2": 200.0,
        "y2": 300.0
      }
    },
    {
      "name": "car",
      "obj_class": 2,
      "confidence": 0.87,
      "box": {
        "x1": 250.0,
        "y1": 400.0,
        "x2": 400.0,
        "y2": 550.0
      }
    }
  ],
  "image_width": 640,
  "image_height": 480
}
```
""";
      case OutputDataType.ClsPredictResults:
        return """
**ClsPredictResults example:**

```json
{
  "image_id": "image_001.jpg",
  "class_id": 5,
  "name": "cat",
  "confidence": 0.92
}
```
""";
    }
  }
}

OutputDataType getOutputDataTypeFromString(String value) {
  switch (value) {
    case 'text':
      return OutputDataType.text;
    case 'PredictResults':
      return OutputDataType.PredictResults;
    case 'ClsPredictResults':
      return OutputDataType.ClsPredictResults;
    default:
      return OutputDataType.text;
  }
}
