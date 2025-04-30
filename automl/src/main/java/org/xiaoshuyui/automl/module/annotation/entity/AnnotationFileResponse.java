package org.xiaoshuyui.automl.module.annotation.entity;

import java.util.List;
import lombok.Data;

@Data
public class AnnotationFileResponse {
  long annotationId;
  String annotationPath;
  List<String> files;
  List<String> classes;
  int storageType;
}
