package org.xiaoshuyui.automl.module.task.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import com.fasterxml.jackson.annotation.JsonIgnore;
import java.time.LocalDateTime;
import lombok.Data;

@Data
@TableName("task")
public class Task {

  @TableId(value = "task_id", type = IdType.AUTO)
  private Integer taskId;

  /** 0 train ;1 eval; 2 others */
  @TableField("task_type")
  private Integer taskType;

  /** dataset id */
  @TableField("dataset_id")
  private Integer datasetId;

  /** annotation id */
  @TableField("annotation_id")
  private Integer annotationId;

  /** 创建时间 */
  @TableField(value = "created_at")
  private LocalDateTime createdAt;

  /** 更新时间 */
  @TableField(value = "updated_at")
  private LocalDateTime updatedAt;

  /** 是否已删除（逻辑删除） */
  @TableField("is_deleted")
  @JsonIgnore
  private Integer isDeleted;

  /** 任务状态 0 pre task, 1 on task,2 post task,3 done, 4 other */
  @TableField("status")
  private Integer status;
}
