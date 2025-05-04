package org.xiaoshuyui.automl.module.annotation.entity;

import lombok.Data;

@Data
public class NewAnnotationRequest {
    Long datasetId;
    // 0:本地 1:s3 2:webdav ...
    int storageType;
    String savePath;
    String username;
    String password;
    // 0:分类 1:检测 2:分割 3:其它
    int type;
    String classes;
}
