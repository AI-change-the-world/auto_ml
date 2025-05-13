package org.xiaoshuyui.automl.module.aether.workflow.action;

import java.util.List;
import org.xiaoshuyui.automl.config.S3ConfigProperties;
import org.xiaoshuyui.automl.module.aether.workflow.AetherWorkflowConfig;
import org.xiaoshuyui.automl.module.aether.workflow.WorkflowAction;
import org.xiaoshuyui.automl.module.aether.workflow.WorkflowContext;
import org.xiaoshuyui.automl.module.aether.workflow.WorkflowStep;
import org.xiaoshuyui.automl.module.annotation.service.AnnotationService;
import org.xiaoshuyui.automl.module.deploy.entity.PredictSingleImageResponse;
import org.xiaoshuyui.automl.util.S3FileDelegate;
import org.xiaoshuyui.automl.util.SpringContextUtil;

public class SaveAnnotationToS3Action extends WorkflowAction {

  private final S3FileDelegate s3FileDelegate;
  private final S3ConfigProperties s3ConfigProperties;
  private final AnnotationService annotationService;

  public SaveAnnotationToS3Action() {
    this.s3FileDelegate = SpringContextUtil.getBean(S3FileDelegate.class);
    this.s3ConfigProperties = SpringContextUtil.getBean(S3ConfigProperties.class);
    this.annotationService = SpringContextUtil.getBean(AnnotationService.class);
  }

  public void execute(WorkflowStep step, WorkflowContext context) {
    var annotationId = (Long) context.get("annotation_id");
    var annotation = annotationService.getById(annotationId);
    if (annotation == null) {
      return;
    }
    String annotationSavePath = annotation.getAnnotationSavePath();
    AetherWorkflowConfig config = step.getAetherConfig();
    PredictSingleImageResponse response = (PredictSingleImageResponse) context.get(config.getInputKey());
    List<String> l = List.of(response.getImage_id().split("/"));
    // List.getLast() 方式估计要求版本比较高，无法适用
    String imageName = l.get(l.size() - 1).substring(0, l.get(l.size() - 1).lastIndexOf("."));
    String annotationSaveFilePath = annotationSavePath + "/" + imageName + ".txt";
    String yoloContent = response.toYoloAnnotation();
    s3FileDelegate.putFile(
        annotationSaveFilePath, yoloContent, s3ConfigProperties.getDatasetsBucketName());
  }
}
