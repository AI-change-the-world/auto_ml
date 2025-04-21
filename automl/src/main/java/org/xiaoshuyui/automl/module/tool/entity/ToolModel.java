package org.xiaoshuyui.automl.module.tool.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import com.fasterxml.jackson.annotation.JsonIgnore;
import lombok.Data;

import java.time.LocalDateTime;

@Data
@TableName("tool_model")
public class ToolModel {
    @TableId(value = "tool_model_id", type = IdType.AUTO)
    Long id;
    @TableField("tool_model_name")
    String name;
    @TableField("tool_model_description")
    String description;
    // 0 llm; 1 M-LLM ;2 vision; 3 others
    @TableField("tool_model_type")
    Integer type;
    // 0 embedded 1 remote
    @TableField("is_embedded")
    Integer isEmbedded;

    @TableField("created_at")
    private LocalDateTime createdAt;

    @TableField("updated_at")
    private LocalDateTime updatedAt;

    @JsonIgnore
    @TableField("is_deleted")
    private Integer isDeleted;

    @TableField("base_url")
    String baseUrl;

    @TableField("api_key")
    String apiKey;

    @TableField("model_name")
    String modelName;
}
