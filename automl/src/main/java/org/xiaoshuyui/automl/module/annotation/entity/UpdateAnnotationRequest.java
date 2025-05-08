package org.xiaoshuyui.automl.module.annotation.entity;

import lombok.Data;

@Data
public class UpdateAnnotationRequest {
    String content;
    String annotationPath;
}
