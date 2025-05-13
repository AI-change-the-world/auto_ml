package org.xiaoshuyui.automl.module.aether.workflow;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.function.Consumer;
import java.util.stream.Collectors;
import lombok.extern.slf4j.Slf4j;

@Slf4j
public class WorkflowEngine {

  private final Map<Integer, WorkflowStep> steps;
  private final WorkflowContext context;

  public WorkflowEngine(List<WorkflowStep> steps, WorkflowContext context) {
    this.steps = steps.stream().collect(Collectors.toMap(WorkflowStep::getId, s -> s));
    this.context = context;
  }

  public WorkflowEngine(List<WorkflowStep> steps) {
    this.steps = steps.stream().collect(Collectors.toMap(WorkflowStep::getId, s -> s));
    this.context = new WorkflowContext();
  }

  public void run(Integer startId) {
    Integer currentStep = startId;

    while (currentStep != null) {
      WorkflowStep step = steps.get(currentStep);
      System.out.println("Running step: " + step.getAetherConfig());
      runStep(step);
      currentStep = step.getNextStepId();
    }
  }

  public void run(Integer startId, boolean sync) {
    if (sync) {
      run(startId);
    } else {
      new Thread(
              () -> {
                Integer currentStep = startId;

                while (currentStep != null) {
                  WorkflowStep step = steps.get(currentStep);
                  System.out.println("Running step: " + step.getAetherConfig());
                  runStep(step);
                  currentStep = step.getNextStepId();
                }
              })
          .start();
    }
  }

  public void run(Integer startId, Consumer<Object> callback) {
    Integer currentStep = startId;
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

      if (step.isLoop()) {
        // 获取循环的数据列表
        String inputKey = step.getInputKey();
        Object listObj = context.get(inputKey);

        if (listObj instanceof List<?>) {
          List<?> list = (List<?>) listObj;
          String loopVar = step.getLoopVar(); // 例如 "item"

          List<Object> resultList = new ArrayList<>();

          for (Object element : list) {
            // 将当前循环的元素注入到上下文中
            context.put(loopVar, element);

            // 执行操作
            action.execute(step, context);

            // 如果这个 action 有输出，收集结果（可选）
            if (step.getOutputKey() != null) {
              Object output = context.get(step.getOutputKey());
              if (output != null) {
                resultList.add(output);
              }
            }
          }

          // 保存聚合输出（如果需要）
          if (step.getOutputKey() != null) {
            context.put(step.getOutputKey(), resultList);
          }

        } else {
          log.error("Expected a List for inputKey: " + inputKey);
        }
      } else {
        // 普通步骤
        action.execute(step, context);
      }

    } catch (Exception e) {
      e.printStackTrace();
    }
  }
}
