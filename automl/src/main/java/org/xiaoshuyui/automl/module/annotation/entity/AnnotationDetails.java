package org.xiaoshuyui.automl.module.annotation.entity;

import java.util.List;
import lombok.Data;

@Data
public class AnnotationDetails {
  Long fileCount;
  List<CountMap> labelCountMap;

  @Data
  public static class CountMap {
    String name;
    Long count;
  }
}
