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
      return "Dataset evalation";
    default:
      return "Other";
  }
}

String taskStatusToString(int status) {
  switch (status) {
    case 0:
      return "Pre task";
    case 1:
      return "On task";
    case 2:
      return "Post task";
    case 3:
      return "Task done";
    default:
      return "other";
  }
}
