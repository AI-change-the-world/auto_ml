package org.xiaoshuyui.automl.module.job.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import com.fasterxml.jackson.annotation.JsonIgnore;
import lombok.Data;

import java.time.LocalDateTime;

@Data
@TableName("job")
public class Job {
    @TableId(value = "job_id", type = IdType.AUTO)
    Long id;
    @TableField(value = "dataset_id")
    Long datasetId;

    /// 0:未开始 1:进行中 2:已完成 3:失败
    @TableField(value = "job_status")
    Integer status;

    /// 0:标注 1:模型训练 2:数据扫描
    @TableField(value = "job_type")
    Integer type;

    @TableField(value = "error_message")
    String message;

    @TableField("created_at")
    LocalDateTime createdAt;
    @TableField("updated_at")
    LocalDateTime updatedAt;

    @JsonIgnore
    @TableField("is_deleted")
    Integer isDeleted;
}
