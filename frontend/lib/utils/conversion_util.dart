// 0: image, 1: text, 2: video, 3: audio, 4: other
String datatypeToString(int datatype) {
  switch (datatype) {
    case 0:
      return "image";
    case 1:
      return "text";
    case 2:
      return "video";
    case 3:
      return "audio";
    default:
      return "other";
  }
}

String taskTypeToString(int datatype) {
  switch (datatype) {
    case 0:
      return "Train";
    case 1:
      return "Test";
    case 2:
      return "video";
    default:
      return "other";
  }
}
