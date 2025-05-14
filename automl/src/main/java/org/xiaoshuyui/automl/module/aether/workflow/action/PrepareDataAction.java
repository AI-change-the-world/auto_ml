package org.xiaoshuyui.automl.module.aether.workflow.action;

import java.util.ArrayList;
import java.util.List;
import org.xiaoshuyui.automl.config.S3ConfigProperties;
import org.xiaoshuyui.automl.module.aether.workflow.WorkflowAction;
import org.xiaoshuyui.automl.module.aether.workflow.WorkflowContext;
import org.xiaoshuyui.automl.module.aether.workflow.WorkflowStep;
import org.xiaoshuyui.automl.util.S3FileDelegate;
import org.xiaoshuyui.automl.util.SpringContextUtil;

public class PrepareDataAction extends WorkflowAction {

  private final S3FileDelegate s3FileDelegate;
  private final S3ConfigProperties s3ConfigProperties;

  public PrepareDataAction() {
    this.s3FileDelegate = SpringContextUtil.getBean(S3FileDelegate.class);
    this.s3ConfigProperties = SpringContextUtil.getBean(S3ConfigProperties.class);
  }

  public void execute(WorkflowStep step, WorkflowContext context) {
    String stepResultId = step.getId() + "_result";
    try {
      var datasetPath = context.get("imgPath", String.class);
      List<String> files =
          s3FileDelegate.listFiles(datasetPath, s3ConfigProperties.getDatasetsBucketName());
      context.put(stepResultId, files);
    } catch (Exception e) {
      e.printStackTrace();
      context.put(stepResultId, new ArrayList<>());
    }
  }
}
