package org.xiaoshuyui.automl.module.aether.workflow;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;

@Data
@AllArgsConstructor
@Builder
public class WorkflowStep {
  private String id;
  private String name;
  private String actionClass;
  private AetherWorkflowConfig aetherConfig;
  private String nextStepId;

  public static WorkflowStep fromConfig(WorkflowStepConfig config) {
    return WorkflowStep.builder()
        .actionClass(config.getAction().getClassName())
        .aetherConfig(config.getAether())
        .id(config.getId())
        .name(config.getName())
        .nextStepId(config.getNext())
        .build();
  }
}
