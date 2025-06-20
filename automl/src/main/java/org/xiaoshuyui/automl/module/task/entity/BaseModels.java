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
@TableName(value = "base_models", autoResultMap = true)
public class BaseModels extends BaseEntity {
  @TableField("base_model_name")
  String name;

  @TableId(value = "base_model_id", type = IdType.AUTO)
  Long id;

  // base model type, 0 classification, 1 detection, 2 segmentation, 3 other
  @TableField("base_model_type")
  Integer type;
}
