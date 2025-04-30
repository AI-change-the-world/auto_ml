package org.xiaoshuyui.automl.module.dataset.entity.response;

import lombok.Data;

@Data
public class DatasetDetailsResponse {
  String samplePath;
  int status;
  long count;
}
