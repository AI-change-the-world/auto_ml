package org.xiaoshuyui.automl.module.tool.entity;

import lombok.Data;

import java.util.List;

@Data
public class PredictRequest {
    private String image_data;
    private List<String> classes;
    private int model_id;
    private String prompt;
}
