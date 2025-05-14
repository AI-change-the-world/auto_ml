package org.xiaoshuyui.automl.module.aether.workflow.action;

import org.xiaoshuyui.automl.module.aether.entity.AetherRequest;
import org.xiaoshuyui.automl.module.aether.entity.AetherResponse;
import org.xiaoshuyui.automl.module.aether.workflow.AetherWorkflowConfig;
import org.xiaoshuyui.automl.module.aether.workflow.WorkflowAction;
import org.xiaoshuyui.automl.module.aether.workflow.WorkflowContext;
import org.xiaoshuyui.automl.module.aether.workflow.WorkflowStep;

public class BatchLabelImageAction extends WorkflowAction {

  @Override
  public void execute(WorkflowStep step, WorkflowContext context) {
    AetherWorkflowConfig config = step.getAetherConfig();

    AetherRequest<Object> request = new AetherRequest<>();
    request.setTask(config.getTask());
    request.setModelId(config.getModelId());

    AetherRequest.Input input = new AetherRequest.Input();
    input.setData((String) context.get(config.getInputKey()));
    input.setDataType(config.getInputType());
    request.setInput(input);

    AetherRequest.Meta meta = new AetherRequest.Meta();
    Long taskId = (Long) context.getOrDefault("taskId", System.currentTimeMillis());
    meta.setTaskId(taskId);
    Boolean sync = (Boolean) context.getOrDefault("sync", true);
    meta.setSync(sync);
    request.setMeta(meta);

    request.setExtra(config.getExtra(context));

    AetherResponse<?> result = aetherClient.invoke(request, Object.class);
    context.put(step.getId() + "_result", result);
    super.execute(step, context);
  }
}
