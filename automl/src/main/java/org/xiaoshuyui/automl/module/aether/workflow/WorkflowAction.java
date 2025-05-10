package org.xiaoshuyui.automl.module.aether.workflow;

public interface WorkflowAction {
  void execute(WorkflowStep step, WorkflowContext context);
}
