package org.xiaoshuyui.automl.module.dataset.entity.response;

import java.util.List;
import lombok.Data;

@Data
public class DatasetDetailsResponse {
  List<String> samples;
  Long usedCount;
}
