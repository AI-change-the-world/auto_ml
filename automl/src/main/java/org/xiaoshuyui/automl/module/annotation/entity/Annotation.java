package org.xiaoshuyui.automl.module.annotation.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

@Data
@TableName("annotation")
public class Annotation {
    @TableId(value = "annotation_id", type = IdType.AUTO)
    Long id;
    @TableField(value = "dataset_id")
    Long datasetId;
    @TableField(exist = false)
    Long annotatedFileCount;
//    @TableField(exist = false)
//    String datasetName;

    // 0:分类 1:检测 2:分割 3:其它
    @TableField(value = "annotation_type")
    Integer annotationType;

    @TableField(value = "updated_at")
    LocalDateTime updatedAt;
    @TableField(value = "is_deleted")
    Integer isDeleted;
    @TableField(value = "created_at")
    LocalDateTime createdAt;
}
