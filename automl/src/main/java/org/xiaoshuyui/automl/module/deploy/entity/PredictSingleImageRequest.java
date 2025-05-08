package org.xiaoshuyui.automl.module.deploy.entity;

import lombok.Data;

@Data
public class PredictSingleImageRequest {
  String data;
  Long modelId;
}
