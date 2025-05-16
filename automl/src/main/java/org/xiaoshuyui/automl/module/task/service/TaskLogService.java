package org.xiaoshuyui.automl.module.task.service;

import org.springframework.stereotype.Service;
import org.xiaoshuyui.automl.module.task.entity.TaskLog;
import org.xiaoshuyui.automl.module.task.mapper.TaskLogMapper;

@Service
public class TaskLogService {
  private final TaskLogMapper taskLogMapper;

  public TaskLogService(TaskLogMapper taskLogMapper) {
    this.taskLogMapper = taskLogMapper;
  }

  public void save(Long taskId, String log) {
    TaskLog taskLog = new TaskLog();
    taskLog.setTaskId(taskId);
    taskLog.setLogContent(log);
    taskLogMapper.insert(taskLog);
  }
}
