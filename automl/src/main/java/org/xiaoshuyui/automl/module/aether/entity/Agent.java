package org.xiaoshuyui.automl.module.aether.entity;

import org.xiaoshuyui.automl.module.BaseEntity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;
import lombok.EqualsAndHashCode;

@Data
@EqualsAndHashCode(callSuper = false)
@TableName(value = "agent", autoResultMap = true)
public class Agent extends BaseEntity {
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

  @TableField(value = "is_recommended")
  Integer isRecommended;

  @TableField(value = "module")
  String module;
}
