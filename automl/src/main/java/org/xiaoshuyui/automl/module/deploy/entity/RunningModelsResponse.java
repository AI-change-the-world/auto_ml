package org.xiaoshuyui.automl.module.deploy.entity;

import java.util.List;
import lombok.Data;

@Data
public class RunningModelsResponse {
  List<Long> running_models;
}
