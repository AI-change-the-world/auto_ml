package org.xiaoshuyui.automl.module.predict.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;

import org.xiaoshuyui.automl.module.BaseEntity;

import lombok.Data;
import lombok.EqualsAndHashCode;

@Data
@EqualsAndHashCode(callSuper = false)
@TableName(value = "predict_task", autoResultMap = true)
public class PredictTask extends BaseEntity {
  @TableId(value = "task_id", type = IdType.AUTO)
  Long id;

  @TableField(value = "session_id")
  String sessionId;

  @TableField("task_data_id")
  Long taskDataId;

  @TableField(value = "task_result")
  String taskResult;

}
