package org.xiaoshuyui.automl.module.dataset.entity.response;

import lombok.Data;

import java.util.List;

@Data
public class DatasetDetailsResponse {
    List<String> filePaths;
    int status;
    long count;
}
