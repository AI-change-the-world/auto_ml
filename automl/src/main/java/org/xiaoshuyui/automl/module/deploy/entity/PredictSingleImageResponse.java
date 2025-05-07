package org.xiaoshuyui.automl.module.deploy.entity;

import lombok.Data;
import java.util.List;

@Data
public class PredictSingleImageResponse {
    private String image_id;
    private List<Result> results;

    @Data
    public static class Result {
        private String name;
        private int obj_class;
        private double confidence;
        private Box box;
    }

    @Data
    public static class Box {
        private double x1;
        private double y1;
        private double x2;
        private double y2;
    }
}