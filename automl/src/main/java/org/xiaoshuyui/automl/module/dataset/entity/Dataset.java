package org.xiaoshuyui.automl.module.dataset.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import com.fasterxml.jackson.annotation.JsonIgnore;
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

    @JsonIgnore
    @TableField("is_deleted")
    Integer isDeleted;

    // 0: image, 1: text ,2: video ,3: audio ,4: other
    @TableField("dataset_type")
    int type;

    @TableField("ranking")
    double ranking;
}
