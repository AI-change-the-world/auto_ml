package org.xiaoshuyui.automl.module.dataset.entity.request;

import lombok.Data;

@Data
public class GetFilePreviewRequest {
  String path;
  int storageType;
  // String baseUrl;
}
