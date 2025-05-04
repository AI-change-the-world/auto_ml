package org.xiaoshuyui.automl.module.tool.entity;

import java.util.List;
import lombok.Data;

@Data
public class PredictRequest {
  private String image_data;
  private List<String> classes;
  private long model_id;
  private String prompt;
}
