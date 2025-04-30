package org.xiaoshuyui.automl.module.task.service;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import java.util.List;
import org.springframework.stereotype.Service;
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

  public List getTaskList(int pageId, int pageSize) {
    IPage page = new Page();
    page.setCurrent(pageId);
    page.setSize(pageSize);
    QueryWrapper queryWrapper = new QueryWrapper();
    queryWrapper.eq("is_deleted", 0);
    var list = taskMapper.selectPage(page, queryWrapper);

    return list.getRecords();
  }

  public List getTaskLogsById(Long id) {
    QueryWrapper queryWrapper = new QueryWrapper();
    queryWrapper.eq("task_id", id);
    return taskLogMapper.selectList(queryWrapper);
  }
}
