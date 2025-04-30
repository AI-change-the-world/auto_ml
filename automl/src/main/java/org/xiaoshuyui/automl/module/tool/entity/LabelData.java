package org.xiaoshuyui.automl.module.tool.entity;

import java.util.List;
import lombok.Data;

@Data
public class LabelData {
  private List<LabelItem> labels;

  @Override
  public String toString() {
    StringBuilder sb = new StringBuilder();
    for (LabelItem label : labels) {
      sb.append(label.toString());
      sb.append("\n");
    }
    return sb.toString();
  }
}
