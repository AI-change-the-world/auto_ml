package org.xiaoshuyui.automl.module.tool;

import lombok.val;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.*;
import org.xiaoshuyui.automl.common.Result;
import org.xiaoshuyui.automl.module.tool.entity.ModelUseRequest;
import org.xiaoshuyui.automl.module.tool.service.ToolModelService;

@RestController
@RequestMapping("/tool-model")
@Slf4j
public class ToolModelController {

  final ToolModelService toolModelService;

  public ToolModelController(ToolModelService toolModelService) {
    this.toolModelService = toolModelService;
  }

  @GetMapping("/list")
  public Result getAll() {
    return Result.OK_data(toolModelService.getAll());
  }

  @GetMapping("/{id}")
  public Result getById(@PathVariable Long id) {
    return Result.OK_data(toolModelService.getById(id));
  }

  @PostMapping("/model/auto-label")
  public Result autoLabel(@RequestBody ModelUseRequest request) {
    val data = toolModelService.getLabel(request);
    if (data == null) {
      return Result.error("Server error");
    }
    return Result.OK_data(data.toString());
  }
}
