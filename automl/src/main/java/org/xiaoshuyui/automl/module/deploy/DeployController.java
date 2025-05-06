package org.xiaoshuyui.automl.module.deploy;

import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.xiaoshuyui.automl.common.PageRequest;
import org.xiaoshuyui.automl.common.PageResult;
import org.xiaoshuyui.automl.common.Result;
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
}
