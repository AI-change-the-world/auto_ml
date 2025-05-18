package org.xiaoshuyui.automl.module.annotation.entity;

import lombok.Data;

@Data
public class UpdateAnnotationPromptRequest {
    Long annotationId;
    String prompt;
}
