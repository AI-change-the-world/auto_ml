package org.xiaoshuyui.automl.module.deploy.entity;

import java.util.List;
import lombok.Data;

@Data
public class PredictSingleImageResponse {
  private String image_id;
  private int image_width;
  private int image_height;
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
    long safetyVestCount = results.stream().filter(r -> "safety vest".equals(r.name)).count();

    sb.append("共检测到 ").append(total).append(" 个目标\n");
    sb.append("人数：").append(personCount).append("\n");
    sb.append("戴安全帽：").append(hardhatCount);
    sb.append("穿安全背心：").append(safetyVestCount);

    return sb.toString();
  }

  public String toYoloAnnotation() {
    StringBuilder sb = new StringBuilder();

    for (PredictSingleImageResponse.Result result : this.getResults()) {
      PredictSingleImageResponse.Box box = result.getBox();

      double x1 = box.getX1();
      double y1 = box.getY1();
      double x2 = box.getX2();
      double y2 = box.getY2();

      double boxWidth = x2 - x1;
      double boxHeight = y2 - y1;
      double xCenter = x1 + boxWidth / 2.0;
      double yCenter = y1 + boxHeight / 2.0;

      // 归一化
      double x = xCenter / image_width;
      double y = yCenter / image_height;
      double w = boxWidth / image_width;
      double h = boxHeight / image_height;

      sb.append(String.format("%d %.6f %.6f %.6f %.6f\n", result.getObj_class(), x, y, w, h));
    }

    return sb.toString().trim(); // 去除最后一个换行符
  }

  public String toYoloAnnotation(List<String> classes) {
    StringBuilder sb = new StringBuilder();

    for (PredictSingleImageResponse.Result result : this.getResults()) {
      PredictSingleImageResponse.Box box = result.getBox();

      double x1 = box.getX1();
      double y1 = box.getY1();
      double x2 = box.getX2();
      double y2 = box.getY2();

      String formatter = "%s: (%f, %f, %f, %f) [confidence: %.6f]\n";
      sb.append(String.format(formatter, result.getName(), x1, y1, x2, y2, result.getConfidence()));
    }

    return sb.toString().trim(); // 去除最后一个换行符
  }
}
