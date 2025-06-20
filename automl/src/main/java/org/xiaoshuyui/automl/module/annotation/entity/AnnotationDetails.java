package org.xiaoshuyui.automl.module.annotation.entity;

import java.util.List;
import lombok.Data;
import lombok.ToString;

@Data
@ToString
public class AnnotationDetails {
  Long fileCount;
  List<CountMap> labelCountMap;

  @Data
  public static class CountMap {
    String name;
    Long count;
  }
}
