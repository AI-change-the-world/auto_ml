package org.xiaoshuyui.automl.module.task.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import com.fasterxml.jackson.annotation.JsonIgnore;
import java.time.LocalDateTime;
import lombok.Data;

@Data
@TableName("base_models")
public class BaseModels {
  @TableField("base_model_name")
  String name;

  @TableId(value = "base_model_id", type = IdType.AUTO)
  Long id;

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

  // base model type, 0 classification, 1 detection, 2 segmentation, 3 other
  @TableField("base_model_type")
  Integer type;
}
