package org.xiaoshuyui.automl.module.aether.workflow;

import java.util.List;
import java.util.Map;
import java.util.function.Consumer;
import java.util.stream.Collectors;
import lombok.extern.slf4j.Slf4j;

@Slf4j
public class WorkflowEngine {

  private final Map<String, WorkflowStep> steps;
  private final WorkflowContext context;

  public WorkflowEngine(List<WorkflowStep> steps, WorkflowContext context) {
    this.steps = steps.stream().collect(Collectors.toMap(WorkflowStep::getId, s -> s));
    this.context = context;
  }

  public WorkflowEngine(List<WorkflowStep> steps) {
    this.steps = steps.stream().collect(Collectors.toMap(WorkflowStep::getId, s -> s));
    this.context = new WorkflowContext();
  }

  public void run(String startId) {
    String currentStep = startId;

    while (currentStep != null) {
      WorkflowStep step = steps.get(currentStep);
      System.out.println("Running step: " + step.getAetherConfig());
      runStep(step);
      currentStep = step.getNextStepId();
    }
  }

  public void run(String startId, Consumer<Object> callback) {
    String currentStep = startId;
    while (currentStep != null) {
      WorkflowStep step = steps.get(currentStep);
      System.out.println("Running step: " + step.getAetherConfig());
      runStep(step);
      var currentStepResultId = startId + "_result";
      var currentStepResult = context.get(currentStepResultId);
      callback.accept(currentStepResult);
      currentStep = step.getNextStepId();
    }
  }

  private void runStep(WorkflowStep step) {
    try {
      log.info("step.getActionClass():  " + step.getActionClass());
      Class<?> clazz = Class.forName(step.getActionClass());
      WorkflowAction action = (WorkflowAction) clazz.getDeclaredConstructor().newInstance();
      action.execute(step, context);
    } catch (Exception e) {
      e.printStackTrace();
    }
  }
}
