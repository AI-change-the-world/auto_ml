package org.xiaoshuyui.automl.util;

import java.util.*;
import java.util.AbstractMap.SimpleEntry;

public class FileAnnotationMerger {

  public static List<SimpleEntry<String, String>> mergeFilesAndAnnotations(
      List<String> files, List<String> annotations) {
    // 建立 annotation 映射（如 'test' -> 'test.txt'）
    Map<String, String> annotationMap = new HashMap<>();
    for (String ann : annotations) {
      annotationMap.put(removeExtension(ann), ann);
    }

    List<SimpleEntry<String, String>> result = new ArrayList<>();

    for (String file : files) {
      String nameWithoutExt = removeExtension(file);
      String matchedAnnotation = annotationMap.getOrDefault(nameWithoutExt, "");
      result.add(new SimpleEntry<>(file, matchedAnnotation));
    }

    return result;
  }

  // 去掉扩展名
  private static String removeExtension(String filepath) {
    String filename = filepath.substring(filepath.lastIndexOf('/') + 1);
    int dotIndex = filename.lastIndexOf('.');
    return (dotIndex != -1) ? filename.substring(0, dotIndex) : filename;
  }

  // 示例用法
  public static void main(String[] args) {
    List<String> files = Arrays.asList("a/b/test.jpg", "a/b/foo.png", "bar.jpeg");
    List<String> annotations = Arrays.asList("test.txt", "bar.json");

    List<SimpleEntry<String, String>> result = mergeFilesAndAnnotations(files, annotations);

    for (SimpleEntry<String, String> pair : result) {
      System.out.println("File: " + pair.getKey() + ", Annotation: " + pair.getValue());
    }
  }
}
