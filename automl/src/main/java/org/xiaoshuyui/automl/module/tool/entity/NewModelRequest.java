package org.xiaoshuyui.automl.module.tool.entity;

import lombok.Data;

@Data
public class NewModelRequest {
  String baseUrl;
  String apiKey;
  String modelName;
  String name;
}
