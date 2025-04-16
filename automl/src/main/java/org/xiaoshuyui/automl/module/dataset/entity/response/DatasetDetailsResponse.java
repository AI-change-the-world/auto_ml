package org.xiaoshuyui.automl.module.dataset.entity.response;

import lombok.Data;

import java.util.List;

@Data
public class DatasetDetailsResponse {
    String samplePath;
    int status;
    long count;
}
