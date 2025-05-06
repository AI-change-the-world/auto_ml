package org.xiaoshuyui.automl.module.task;

import org.springframework.web.bind.annotation.*;
import org.xiaoshuyui.automl.common.PageRequest;
import org.xiaoshuyui.automl.common.Result;
import org.xiaoshuyui.automl.module.task.entity.NewTrainingTaskRequest;
import org.xiaoshuyui.automl.module.task.service.BaseModelsService;
import org.xiaoshuyui.automl.module.task.service.TaskService;

@RestController
@RequestMapping("/task")
public class TaskController {

  final TaskService taskService;
  final BaseModelsService baseModelsService;

  public TaskController(TaskService taskService, BaseModelsService baseModelsService) {
    this.taskService = taskService;
    this.baseModelsService = baseModelsService;
  }

  @PostMapping("/list")
  public Result getTaskList(@RequestBody PageRequest request) {
    return Result.OK_data(taskService.getTaskList(request.getPageId(), request.getPageSize()));
  }

  @GetMapping("/{id}/logs")
  public Result getTaskLogsById(@PathVariable Long id) {
    return Result.OK_data(taskService.getTaskLogsById(id));
  }

  @GetMapping("/base-models/list")
  public Result getMethodName() {
    return Result.OK_data(baseModelsService.getBaseModels());
  }

  @GetMapping("/base-models/list/{type}")
  public Result getMethodName(@PathVariable Integer type) {
    return Result.OK_data(baseModelsService.getModelsByType(type));
  }

  @PostMapping("/create/train")
  public Result createNewTrainingTask(@RequestBody NewTrainingTaskRequest entity) {
    taskService.newTrainTask(entity);

    return Result.OK();
  }
}
