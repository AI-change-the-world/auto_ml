package org.xiaoshuyui.automl.module.dataset.entity.response;

import lombok.Data;

import java.util.List;

@Data
public class DatasetFileListResponse {
    long datasetId;
    long count;
    List<String> files;
    int datasetType;
    int storageType;
    String datasetBaseUrl;
}
