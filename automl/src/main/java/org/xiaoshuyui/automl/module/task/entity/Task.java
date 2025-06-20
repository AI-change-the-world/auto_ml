package org.xiaoshuyui.automl.module.task.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;

import org.xiaoshuyui.automl.module.BaseEntity;

import lombok.Data;
import lombok.EqualsAndHashCode;

@Data
@EqualsAndHashCode(callSuper = false)
@TableName(value = "task", autoResultMap = true)
public class Task extends BaseEntity {

  @TableId(value = "task_id", type = IdType.AUTO)
  private Long taskId;

  @TableField("task_type")
  private String taskType;

  /** dataset id */
  @TableField("dataset_id")
  private Long datasetId;

  /** annotation id */
  @TableField("annotation_id")
  private Long annotationId;

  /** 任务状态 0 pre task, 1 on task,2 post task,3 done, 4 other */
  @TableField("status")
  private Integer status;

  @TableField("task_config")
  private String taskConfig;
}
