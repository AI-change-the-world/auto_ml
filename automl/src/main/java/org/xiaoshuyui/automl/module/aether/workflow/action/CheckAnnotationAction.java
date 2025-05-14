package org.xiaoshuyui.automl.module.aether.workflow.action;

import com.google.gson.Gson;
import com.google.gson.internal.LinkedTreeMap;
import com.google.gson.reflect.TypeToken;
import java.lang.reflect.Type;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import lombok.extern.slf4j.Slf4j;
import org.xiaoshuyui.automl.module.aether.entity.AetherRequest;
import org.xiaoshuyui.automl.module.aether.entity.AetherResponse;
import org.xiaoshuyui.automl.module.aether.workflow.AetherWorkflowConfig;
import org.xiaoshuyui.automl.module.aether.workflow.WorkflowAction;
import org.xiaoshuyui.automl.module.aether.workflow.WorkflowContext;
import org.xiaoshuyui.automl.module.aether.workflow.WorkflowStep;
import org.xiaoshuyui.automl.module.annotation.service.AnnotationService;
import org.xiaoshuyui.automl.module.deploy.entity.PredictSingleImageResponse;
import org.xiaoshuyui.automl.util.SpringContextUtil;

@Slf4j
public class CheckAnnotationAction extends WorkflowAction {

  static final Gson gson = new Gson();
  private final AnnotationService annotationService;

  public CheckAnnotationAction() {
    this.annotationService = SpringContextUtil.getBean(AnnotationService.class);
  }

  public void execute(WorkflowStep step, WorkflowContext context) {
    var annotationId = (Integer) context.get("annotation_id");
    var annotation = annotationService.getById((long) annotationId);
    if (annotation == null) {
      var key = step.getOutputKey();
      if (key == null) {
        key = step.getId() + "_result";
      }
      context.put(key, null);
      log.error("annotation not found");
      return;
    }
    List<String> annotationClasses = List.of(annotation.getClassItems().split(";"));

    AetherWorkflowConfig config = step.getAetherConfig();
    log.info("config.getInputKey()   :" + config.getInputKey());
    // AetherResponse<PredictSingleImageResponse> response =
    // (AetherResponse<PredictSingleImageResponse>) context
    // .get(config.getInputKey());
    Object raw = context.get(config.getInputKey());

    AetherResponse<?> tempResponse;
    if (raw instanceof LinkedTreeMap) {
      // 先反序列化外层
      String json = gson.toJson(raw);
      Type type = new TypeToken<AetherResponse<Object>>() {}.getType();
      tempResponse = gson.fromJson(json, type);
    } else {
      tempResponse = (AetherResponse<?>) raw;
    }

    // 手动反序列化内部 output 字段
    String outputJson = gson.toJson(tempResponse.getOutput());
    PredictSingleImageResponse realOutput =
        gson.fromJson(outputJson, PredictSingleImageResponse.class);
    String annotations = realOutput.toYoloAnnotation(annotationClasses);

    // context.put(config.getInputKey(), realOutput.getImage_id());
    // context.put("annotations", annotations);

    AetherRequest<Object> request = new AetherRequest<>();
    request.setTask(config.getTask());
    request.setModelId(config.getModelId());
    AetherRequest.Input input = new AetherRequest.Input();
    input.setData(realOutput.getImage_id());
    input.setDataType(config.getInputType());
    request.setInput(input);

    AetherRequest.Meta meta = new AetherRequest.Meta();
    Long taskId = (Long) context.getOrDefault("taskId", System.currentTimeMillis());
    meta.setTaskId(taskId);
    Boolean sync = (Boolean) context.getOrDefault("sync", true);
    meta.setSync(sync);
    request.setMeta(meta);

    Map<String, Object> extra = new HashMap<>();
    extra.put("annotations", annotations);
    extra.put("annotation_id", annotationId);

    request.setExtra(extra);
    AetherResponse<?> result = aetherClient.invoke(request, Object.class);
    context.put(step.getId() + "_result", result);
  }
}
