package org.xiaoshuyui.automl.module.tool.entity;

import lombok.Data;

@Data
public class TryModel {
     String baseUrl;
     String apiKey;
     String modelName;
     // message or base64
     String content;
}
