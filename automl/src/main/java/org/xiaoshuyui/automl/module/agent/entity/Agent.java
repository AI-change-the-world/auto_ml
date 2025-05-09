package org.xiaoshuyui.automl.module.agent.entity;

import java.time.LocalDateTime;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import com.fasterxml.jackson.annotation.JsonIgnore;

import lombok.Data;

@Data
@TableName("agent")
public class Agent {
    @TableId(value = "agent_id", type = IdType.AUTO)
    Long agentId;

    @TableField("agent_name")
    String agentName;

    @TableField("description")
    String description;

    @TableField("pipeline_file_path")
    String pipelineFilePath;

    @TableField("pipeline_content")
    String pipelineContent;

    @TableField("is_embedded")
    int isEmbedded;

    @TableField("created_at")
    LocalDateTime createdAt;

    @TableField("updated_at")
    LocalDateTime updatedAt;

    @JsonIgnore
    @TableField("is_deleted")
    Integer isDeleted;
}
