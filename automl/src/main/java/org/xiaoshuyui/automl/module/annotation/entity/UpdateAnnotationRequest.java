package org.xiaoshuyui.automl.module.annotation.entity;

import lombok.Data;

@Data
public class UpdateAnnotationRequest {
    String annotationPath;
    String content;
}
