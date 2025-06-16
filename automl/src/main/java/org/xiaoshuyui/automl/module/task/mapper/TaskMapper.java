package org.xiaoshuyui.automl.module.task.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import java.util.List;

import org.apache.ibatis.annotations.Param;
import org.xiaoshuyui.automl.module.home.entity.HomeIndex.TaskPerDay;
import org.xiaoshuyui.automl.module.task.entity.Task;

public interface TaskMapper extends BaseMapper<Task> {

  List<TaskPerDay> getTaskPerDay(@Param("days") Integer days);
}
