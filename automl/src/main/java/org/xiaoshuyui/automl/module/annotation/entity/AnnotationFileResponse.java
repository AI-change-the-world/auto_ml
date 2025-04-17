package org.xiaoshuyui.automl.module.annotation.entity;

import lombok.Data;

import java.util.List;

@Data
public class AnnotationFileResponse {
    long annotationId;
    String annotationPath;
    List<String> files;
    List<String> classes;
    int storageType;
}
