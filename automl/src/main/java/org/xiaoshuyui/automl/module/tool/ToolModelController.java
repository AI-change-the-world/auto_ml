package org.xiaoshuyui.automl.module.tool;

import lombok.extern.slf4j.Slf4j;
import lombok.val;
import org.springframework.web.bind.annotation.*;
import org.xiaoshuyui.automl.common.Result;
import org.xiaoshuyui.automl.module.task.service.TaskService;
import org.xiaoshuyui.automl.module.tool.entity.EvalDatasetRequest;
import org.xiaoshuyui.automl.module.tool.entity.FindSimilarObjectRequest;
import org.xiaoshuyui.automl.module.tool.entity.ModelUseRequest;
import org.xiaoshuyui.automl.module.tool.entity.MultipleClassAnnotateRequest;
import org.xiaoshuyui.automl.module.tool.entity.NewModelRequest;
import org.xiaoshuyui.automl.module.tool.service.ToolModelService;

@RestController
@RequestMapping("/tool-model")
@Slf4j
public class ToolModelController {

  final ToolModelService toolModelService;
  final TaskService taskService;

  public ToolModelController(ToolModelService toolModelService, TaskService taskService) {
    this.toolModelService = toolModelService;
    this.taskService = taskService;
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

  @PostMapping("/model/auto-label/multiple")
  public Result autoLabelMultiObj(@RequestBody MultipleClassAnnotateRequest request) {
    // TODO : tool model id
    val data = toolModelService.getMultipleClasses(request.getAnnotationId(), request.getImgPath(), 1L);
    if (data == null) {
      return Result.error("Server error");
    }
    return Result.OK_data(data);
  }

  @PostMapping("/find/similar")
  public Result postMethodName(@RequestBody FindSimilarObjectRequest entity) {
    var res = toolModelService.findSimilar(entity);
    if (res == null) {
      return Result.error("Server error");
    }
    return Result.OK_data(res);
  }

  @PostMapping("/evalation/dataset")
  public Result evalDataset(@RequestBody EvalDatasetRequest entity) {
    taskService.newDatasetEvalationTask(entity.getDatasetId(), entity.getAnnotationId());
    return Result.OK();
  }

  @PostMapping("/new")
  public Result newModel(@RequestBody NewModelRequest entity) throws Exception {
    toolModelService.addNewModel(entity);

    return Result.OK();
  }

}
