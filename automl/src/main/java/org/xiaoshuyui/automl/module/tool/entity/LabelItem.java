package org.xiaoshuyui.automl.module.tool.entity;

import lombok.Data;

@Data
public class LabelItem {
    private String label;
    private double x_center;
    private double y_center;
    private double width;
    private double height;
    private double confidence;

    @Override
    public String toString(){
        return label+" "+x_center+" "+y_center+" "+width+" "+height +" "+confidence;
    }
}
