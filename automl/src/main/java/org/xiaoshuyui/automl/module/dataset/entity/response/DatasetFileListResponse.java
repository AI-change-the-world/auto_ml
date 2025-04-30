package org.xiaoshuyui.automl.module.dataset.entity.response;

import java.util.List;
import lombok.Data;

@Data
public class DatasetFileListResponse {
  long datasetId;
  long count;
  List<String> files;
  int datasetType;
  int storageType;
  String datasetBaseUrl;
}
