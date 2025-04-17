List<(String, String)> mergeFilesAndAnnotations(
  List<String> files,
  List<String> annotations,
) {
  // 建立 annotation 映射（如 'test' -> 'test.txt'）
  final annotationMap = {
    for (var ann in annotations) _removeExtension(ann): ann,
  };

  final result = <(String, String)>[];

  for (var file in files) {
    final nameWithoutExt = _removeExtension(file);
    final matchedAnnotation = annotationMap[nameWithoutExt];
    result.add((file, matchedAnnotation ?? ''));
  }

  return result;
}

// 去掉扩展名
String _removeExtension(String filename) {
  final dotIndex = filename.lastIndexOf('.');
  return (dotIndex != -1) ? filename.substring(0, dotIndex) : filename;
}
