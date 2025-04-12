package org.xiaoshuyui.automl.module.dataset.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

@Data
@TableName("dataset")
public class Dataset {
    @TableId(value = "dataset_id", type = IdType.AUTO)
    Long id;
    @TableField("dataset_name")
    String name;
    @TableField("description")
    String description;
    @TableField("created_at")
    LocalDateTime createdAt;
    @TableField("updated_at")
    LocalDateTime updatedAt;
    @TableField("is_deleted")
    Integer isDeleted;
}
