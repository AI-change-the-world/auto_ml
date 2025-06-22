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
