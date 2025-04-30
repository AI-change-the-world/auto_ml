package org.xiaoshuyui.automl.module.task.entity;

import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableName;
import java.time.LocalDateTime;
import lombok.Data;

@TableName("task_log")
@Data
public class TaskLog {
  @TableField("task_id")
  private Long taskId;

  @TableField("log_content")
  private String logContent;

  @TableField("created_at")
  private LocalDateTime createdAt;
}
