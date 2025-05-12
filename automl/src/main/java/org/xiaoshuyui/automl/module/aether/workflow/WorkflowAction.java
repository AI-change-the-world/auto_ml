package org.xiaoshuyui.automl.module.aether.workflow;

import org.xiaoshuyui.automl.module.aether.AetherClient;
import org.xiaoshuyui.automl.util.SpringContextUtil;

public class WorkflowAction {

  protected final AetherClient aetherClient;

  public WorkflowAction() {
    this.aetherClient = SpringContextUtil.getBean(AetherClient.class);
  }

  public void execute(WorkflowStep step, WorkflowContext context) {
    String outputKey = step.getOutputKey();
    if (outputKey != null) {
      context.put(step.getId() + "_outputKey", outputKey);
    }
    String outputKeyType = step.getOutputKeyType();
    if (outputKeyType != null) {
      context.put(step.getId() + "_outputKeyType", outputKeyType);
    }
  }
}
