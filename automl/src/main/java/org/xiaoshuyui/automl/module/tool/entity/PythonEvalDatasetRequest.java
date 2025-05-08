package org.xiaoshuyui.automl.module.tool.entity;

import lombok.Data;

@Data
public class PythonEvalDatasetRequest {
  Long dataset_id;
  Long annotation_id;
  Long task_id;
}
