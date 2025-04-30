package org.xiaoshuyui.automl.module.annotation.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import java.time.LocalDateTime;
import lombok.Data;

@Data
@TableName("annotation")
public class Annotation {
  @TableId(value = "annotation_id", type = IdType.AUTO)
  Long id;

  @TableField(value = "dataset_id")
  Long datasetId;

  // 0:分类 1:检测 2:分割 3:其它
  @TableField(value = "annotation_type")
  Integer annotationType;

  @TableField(value = "updated_at")
  LocalDateTime updatedAt;

  @TableField(value = "is_deleted")
  Integer isDeleted;

  @TableField(value = "created_at")
  LocalDateTime createdAt;

  @TableField(value = "class_items")
  String classItems;

  @TableField(value = "annotation_path")
  String annotationPath;

  // 0:本地 1:s3 2:webdav 3:其它
  @TableField(value = "storage_type")
  Integer storageType;
}
