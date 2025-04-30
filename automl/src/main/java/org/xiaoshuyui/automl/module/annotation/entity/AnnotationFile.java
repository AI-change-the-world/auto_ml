package org.xiaoshuyui.automl.module.annotation.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import java.time.LocalDateTime;
import lombok.Data;

@Deprecated(since = "no longer used")
@Data
@TableName("annotation_file")
public class AnnotationFile {
  @TableId(value = "file_id", type = IdType.AUTO)
  Long id;

  @TableField(value = "annotation_id")
  Long annotationId;

  @TableField(value = "file_path")
  String filePath;

  @TableField(value = "updated_at")
  LocalDateTime updatedAt;

  @TableField(value = "is_deleted")
  Integer isDeleted;

  @TableField(value = "created_at")
  LocalDateTime createdAt;
}
