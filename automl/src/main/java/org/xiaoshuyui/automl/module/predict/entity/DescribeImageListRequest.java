package org.xiaoshuyui.automl.module.predict.entity;

import java.util.List;
import lombok.Data;

@Data
public class DescribeImageListRequest {
  List<String> frames;
  String prompt;
  Long model_id;
}
