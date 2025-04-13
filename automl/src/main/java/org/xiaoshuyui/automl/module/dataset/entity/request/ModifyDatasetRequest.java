package org.xiaoshuyui.automl.module.dataset.entity.request;

import lombok.Data;

@Data
public class ModifyDatasetRequest {
    String name;
    String description;
    // 0:本地 1:s3 2:webdav ...
    int storageType;
    String url;
    String username;
    String password;
    Long id;
    double ranking;
}
