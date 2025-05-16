package org.xiaoshuyui.automl.module.aether.workflow.action;

import com.google.gson.Gson;
import com.google.gson.internal.LinkedTreeMap;
import com.google.gson.reflect.TypeToken;
import java.lang.reflect.Type;
import java.util.List;
import lombok.extern.slf4j.Slf4j;
import org.xiaoshuyui.automl.config.S3ConfigProperties;
import org.xiaoshuyui.automl.module.aether.entity.AetherResponse;
import org.xiaoshuyui.automl.module.aether.workflow.AetherWorkflowConfig;
import org.xiaoshuyui.automl.module.aether.workflow.WorkflowAction;
import org.xiaoshuyui.automl.module.aether.workflow.WorkflowContext;
import org.xiaoshuyui.automl.module.aether.workflow.WorkflowStep;
import org.xiaoshuyui.automl.module.annotation.service.AnnotationService;
import org.xiaoshuyui.automl.module.deploy.entity.PredictSingleImageResponse;
import org.xiaoshuyui.automl.util.S3FileDelegate;
import org.xiaoshuyui.automl.util.SpringContextUtil;

@Slf4j
public class SaveAnnotationToS3Action extends WorkflowAction {

  private final S3FileDelegate s3FileDelegate;
  private final S3ConfigProperties s3ConfigProperties;
  private final AnnotationService annotationService;

  public SaveAnnotationToS3Action() {
    this.s3FileDelegate = SpringContextUtil.getBean(S3FileDelegate.class);
    this.s3ConfigProperties = SpringContextUtil.getBean(S3ConfigProperties.class);
    this.annotationService = SpringContextUtil.getBean(AnnotationService.class);
  }

  static final Gson gson = new Gson();

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
    String annotationSavePath = annotation.getAnnotationSavePath();
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

    List<String> l = List.of(realOutput.getImage_id().split("/"));
    // List.getLast() 方式估计要求版本比较高，无法适用
    String imageName = l.get(l.size() - 1).substring(0, l.get(l.size() - 1).lastIndexOf("."));
    String annotationSaveFilePath = annotationSavePath + "/" + imageName + ".txt";
    String yoloContent = realOutput.toYoloAnnotation();
    log.info("yolo content ====> " + yoloContent);
    s3FileDelegate.putFile(
        annotationSaveFilePath, yoloContent, s3ConfigProperties.getDatasetsBucketName());
  }
}
