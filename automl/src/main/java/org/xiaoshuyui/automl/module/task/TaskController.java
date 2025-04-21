package org.xiaoshuyui.automl.module.task;

import org.springframework.web.bind.annotation.*;
import org.xiaoshuyui.automl.common.PageRequest;
import org.xiaoshuyui.automl.common.Result;
import org.xiaoshuyui.automl.module.task.service.TaskService;

@RestController
@RequestMapping("/task")
public class TaskController {

    final TaskService taskService;

    public TaskController(TaskService taskService) {
        this.taskService = taskService;
    }

    @PostMapping("/list")
    public Result getTaskList(@RequestBody PageRequest request) {
        return Result.OK_data(taskService.getTaskList(request.getPageId(), request.getPageSize()));
    }

    @PostMapping("/{id}/logs")
    public Result getTaskLogsById(@PathVariable Long id) {
        return Result.OK_data(taskService.getTaskLogsById(id));
    }
}
