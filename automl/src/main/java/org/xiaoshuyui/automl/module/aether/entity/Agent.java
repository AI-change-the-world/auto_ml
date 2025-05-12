package org.xiaoshuyui.automl.module.aether.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import com.fasterxml.jackson.annotation.JsonIgnore;
import java.time.LocalDateTime;
import lombok.Data;

@Data
@TableName("agent")
public class Agent {
  @TableId(value = "agent_id", type = IdType.AUTO)
  Long id;

  @TableField("agent_name")
  String name;

  @TableField("description")
  String description;

  @Deprecated
  @TableField("pipeline_file_path")
  String pipelineFilePath;

  @TableField("pipeline_content")
  String pipelineContent;

  @TableField("is_embedded")
  Integer isEmbedded;

  @TableField(value = "updated_at")
  LocalDateTime updatedAt;

  @JsonIgnore
  @TableField(value = "is_deleted")
  Integer isDeleted;

  @TableField(value = "created_at")
  LocalDateTime createdAt;

  @TableField(value = "is_recommended")
  Integer isRecommended;

  @TableField(value = "module")
  String module;
}
