package org.xiaoshuyui.automl.module.predict.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import com.fasterxml.jackson.annotation.JsonIgnore;
import lombok.Data;

import java.time.LocalDateTime;

@Data
@TableName("predict_task")
public class PredictTask {
    @TableId(value = "task_id", type = IdType.AUTO)
    Long id;
    @TableField(value = "session_id")
    String sessionId;
    @TableField("task_data_id")
    Long taskDataId;

    @TableField(value = "task_result")
    String taskResult;

    /**
     * 创建时间
     */
    @TableField(value = "created_at")
    private LocalDateTime createdAt;

    /**
     * 更新时间
     */
    @TableField(value = "updated_at")
    private LocalDateTime updatedAt;

    /**
     * 是否已删除（逻辑删除）
     */
    @TableField("is_deleted")
    @JsonIgnore
    private Integer isDeleted;
}
