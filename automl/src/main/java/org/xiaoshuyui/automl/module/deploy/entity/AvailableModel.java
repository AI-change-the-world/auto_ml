package org.xiaoshuyui.automl.module.deploy.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;

import org.xiaoshuyui.automl.module.BaseEntity;

import lombok.Data;
import lombok.EqualsAndHashCode;

@TableName(value = "available_models", autoResultMap = true)
@Data
@EqualsAndHashCode(callSuper = false)
public class AvailableModel extends BaseEntity {
  @TableId(value = "available_model_id", type = IdType.AUTO)
  Long id;

  @TableField("save_path")
  String savePath;

  @TableField("base_model_name")
  String baseModelName;

  @TableField("loss")
  double loss;

  @TableField("epoch")
  int epoch;

  @TableField("dataset_id")
  Long datasetId;

  @TableField("annotation_id")
  Long annotationId;

  @TableField("model_type")
  String modelType;
}
