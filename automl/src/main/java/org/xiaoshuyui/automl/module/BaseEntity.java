package org.xiaoshuyui.automl.module;

import java.time.LocalDateTime;

import com.baomidou.mybatisplus.annotation.FieldStrategy;
import com.baomidou.mybatisplus.annotation.TableField;
import com.fasterxml.jackson.annotation.JsonIgnore;

import lombok.Data;

@Data
public class BaseEntity {

    @TableField(value = "updated_at", updateStrategy = FieldStrategy.NEVER)
    LocalDateTime updatedAt;

    @JsonIgnore
    @TableField(value = "is_deleted")
    Integer isDeleted;

    @TableField(value = "created_at")
    LocalDateTime createdAt;

}