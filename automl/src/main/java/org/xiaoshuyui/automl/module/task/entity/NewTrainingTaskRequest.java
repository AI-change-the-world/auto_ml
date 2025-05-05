package org.xiaoshuyui.automl.module.task.entity;

import lombok.Data;

@Data
public class NewTrainingTaskRequest {
    String name;
    int size;
    int batch;
    int epoch;
    long datasetId;
    long annotationId;
}
