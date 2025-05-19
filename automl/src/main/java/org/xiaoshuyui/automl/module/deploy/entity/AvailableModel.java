package org.xiaoshuyui.automl.module.deploy.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import com.fasterxml.jackson.annotation.JsonIgnore;
import java.time.LocalDateTime;
import lombok.Data;

@TableName("available_models")
@Data
public class AvailableModel {
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

  @TableField("created_at")
  LocalDateTime createdAt;

  @TableField("updated_at")
  LocalDateTime updatedAt;

  @JsonIgnore
  @TableField("is_deleted")
  Integer isDeleted;

  @TableField("model_type")
  String modelType;
}
