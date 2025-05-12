package org.xiaoshuyui.automl.module.deploy.entity;

import java.util.List;
import lombok.Data;

@Data
public class PredictSingleImageResponse {
  private String image_id;
  private List<Result> results;

  @Data
  public static class Result {
    private String name;
    private int obj_class;
    private double confidence;
    private Box box;
  }

  @Data
  public static class Box {
    private double x1;
    private double y1;
    private double x2;
    private double y2;
  }

  @Override
  public String toString() {
    StringBuilder sb = new StringBuilder();

    int total = results != null ? results.size() : 0;
    long personCount = results.stream().filter(r -> "person".equals(r.name)).count();
    long hardhatCount = results.stream().filter(r -> "hat".equals(r.name)).count();
    long safetyVestCount = results.stream()
        .filter(r -> "safety vest".equals(r.name))
        .count();

    sb.append("共检测到 ").append(total).append(" 个目标\n");
    sb.append("人数：").append(personCount).append("\n");
    sb.append("戴安全帽：").append(hardhatCount);
    sb.append("穿安全背心：").append(safetyVestCount);

    return sb.toString();
  }
}
