package org.xiaoshuyui.automl.module.task.service;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import java.util.List;
import org.springframework.stereotype.Service;
import org.xiaoshuyui.automl.common.PageResult;
import org.xiaoshuyui.automl.module.task.entity.Task;
import org.xiaoshuyui.automl.module.task.mapper.TaskLogMapper;
import org.xiaoshuyui.automl.module.task.mapper.TaskMapper;

@Service
public class TaskService {

  private final TaskMapper taskMapper;
  private final TaskLogMapper taskLogMapper;

  public TaskService(TaskMapper taskMapper, TaskLogMapper taskLogMapper) {
    this.taskMapper = taskMapper;
    this.taskLogMapper = taskLogMapper;
  }

  public PageResult getTaskList(int pageId, int pageSize) {
    IPage<Task> page = new Page<>(pageId, pageSize);
    QueryWrapper<Task> queryWrapper = new QueryWrapper<>();
    queryWrapper.eq("is_deleted", 0);

    IPage<Task> resultPage = taskMapper.selectPage(page, queryWrapper);

    return new PageResult<>(resultPage.getRecords(), resultPage.getTotal());
  }

  public List getTaskLogsById(Long id) {
    QueryWrapper queryWrapper = new QueryWrapper();
    queryWrapper.eq("task_id", id);
    return taskLogMapper.selectList(queryWrapper);
  }
}
