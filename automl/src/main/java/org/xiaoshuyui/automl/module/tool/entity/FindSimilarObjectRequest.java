package org.xiaoshuyui.automl.module.tool.entity;

import lombok.Data;

/*
 * 
 * class FindSimilarRequest(BaseModel):
    path: str
    left: float
    top: float
    right: float
    bottom: float
    label: str
    model: int
    id: int
*/
@Data
public class FindSimilarObjectRequest {
    String path;
    double left;
    double top;
    double right;
    double bottom;
    String label;
    // model id
    int model;
    // annotation id
    int id;
}
