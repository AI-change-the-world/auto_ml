package org.xiaoshuyui.automl.module.tool.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import com.fasterxml.jackson.annotation.JsonIgnore;

import org.xiaoshuyui.automl.module.BaseEntity;

import lombok.Data;
import lombok.EqualsAndHashCode;

@Data
@EqualsAndHashCode(callSuper = false)
@TableName(value = "tool_model", autoResultMap = true)
public class ToolModel extends BaseEntity {
  @TableId(value = "tool_model_id", type = IdType.AUTO)
  Long id;

  @TableField("tool_model_name")
  String name;

  @TableField("tool_model_description")
  String description;

  // 0 llm; 1 M-LLM ;2 vision; 3 others
  @TableField("tool_model_type")
  String type;

  // 0 embedded 1 remote
  @TableField("is_embedded")
  Integer isEmbedded;

  @JsonIgnore
  @TableField("base_url")
  String baseUrl;

  @JsonIgnore
  @TableField("api_key")
  String apiKey;

  @JsonIgnore
  @TableField("model_name")
  String modelName;
}
