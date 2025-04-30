package org.xiaoshuyui.automl.module.tool.entity;

import lombok.Data;

@Data
public class ModelUseRequest {
  boolean isImage;
  String content;
  String prompt;
  long modelId;
  long annotationId;

  long datasetId;
}
