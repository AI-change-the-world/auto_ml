package org.xiaoshuyui.automl.module.predict.entity;

import lombok.Data;

@Data
public class ProcessRequest {
    Long fileId;
    // reserved for future use
    Long methodId;  // or agent id
}
