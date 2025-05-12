package org.xiaoshuyui.automl.module.aether.workflow;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;

@Data
@AllArgsConstructor
@Builder
public class WorkflowStep {
  private int id;
  private String name;
  private String actionClass;
  private AetherWorkflowConfig aetherConfig;
  private Integer nextStepId;
  private String outputKey;
  private String outputKeyType;

  public static WorkflowStep fromConfig(WorkflowStepConfig config) {
    return WorkflowStep.builder()
        .actionClass(config.getAction().getClassName())
        .aetherConfig(config.getAether())
        .id(config.getId())
        .name(config.getName())
        .nextStepId(config.getNext())
        .outputKey(config.getOutputKey())
        .outputKeyType(config.getOutputType())
        .build();
  }
}
