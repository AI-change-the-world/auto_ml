package org.xiaoshuyui.automl.module.deploy.entity;

import lombok.Data;

/*
 * {
    "name": "solar_dish",
    "class": 807,
    "confidence": 0.32724
  }
*/

@Data
public class PredictClassificationSingleImageResponse {
  private String image_id;
  private String name;
  private int class_id;
  private double confidence;
}
