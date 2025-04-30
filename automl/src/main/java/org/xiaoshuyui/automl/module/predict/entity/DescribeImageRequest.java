package org.xiaoshuyui.automl.module.predict.entity;

import lombok.Data;

@Data
public class DescribeImageRequest {
  String prompt;
  String frame_path;
  Long model_id;
}
