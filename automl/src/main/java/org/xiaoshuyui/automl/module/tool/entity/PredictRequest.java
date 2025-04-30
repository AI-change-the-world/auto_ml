package org.xiaoshuyui.automl.module.tool.entity;

import java.util.List;
import lombok.Data;

@Data
public class PredictRequest {
  private String image_data;
  private List<String> classes;
  private int model_id;
  private String prompt;
}
