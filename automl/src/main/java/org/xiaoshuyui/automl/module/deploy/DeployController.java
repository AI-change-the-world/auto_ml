package org.xiaoshuyui.automl.module.deploy;

import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.xiaoshuyui.automl.common.PageRequest;
import org.xiaoshuyui.automl.common.PageResult;
import org.xiaoshuyui.automl.common.Result;
import org.xiaoshuyui.automl.module.deploy.entity.PredictSingleImageRequest;
import org.xiaoshuyui.automl.module.deploy.entity.RunningModelsResponse;
import org.xiaoshuyui.automl.module.deploy.service.AvailableModelService;

@RequestMapping("/deploy")
@RestController
@Slf4j
public class DeployController {

  private final AvailableModelService availableModelService;

  public DeployController(AvailableModelService availableModelService) {
    this.availableModelService = availableModelService;
  }

  @PostMapping("/available-models/list")
  public Result getAvailableModels(@RequestBody PageRequest pageRequest) {
    PageResult pageResult = availableModelService.getAvailableModels(pageRequest);
    return Result.OK_data(pageResult);
  }

  @GetMapping("/running-models")
  public Result getRunningModels() {
    RunningModelsResponse response = availableModelService.getRunningModels();
    return Result.OK_data(response);
  }

  @GetMapping("/start/{id}")
  public Result startModel(@PathVariable Long id) {
    int r = availableModelService.startModel(id);
    if (r == 0) {
      return Result.OK();
    } else {
      return Result.error("启动模型失败");
    }
  }

  @GetMapping("/stop/{id}")
  public Result stopModel(@PathVariable Long id) {
    int r = availableModelService.stopModel(id);
    if (r == 0) {
      return Result.OK();
    } else {
      return Result.error("关闭模型失败");
    }
  }

  @PostMapping("/predict/image")
  public Result predictSingleImage(@RequestBody PredictSingleImageRequest entity) {
    var model = availableModelService.getAvailableModelById(entity.getModelId());
    if (model == null) {
      return Result.error("模型不存在");
    }
    Object d;
    if (model.getModelType().equals("classification")) {
      d = availableModelService.predictClsSingleImage(entity);
    } else {
      d = availableModelService.predictSingleImage(entity);
    }

    if (d != null) {
      return Result.OK_data(d);
    } else {
      return Result.error("预测失败");
    }
  }
}
