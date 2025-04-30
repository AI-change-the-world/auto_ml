package org.xiaoshuyui.automl.module.predict.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import com.fasterxml.jackson.annotation.JsonIgnore;
import java.time.LocalDateTime;
import lombok.Data;

@Data
@TableName("predict_data")
public class PredictData {
  @TableId(value = "predict_data_id", type = IdType.AUTO)
  Long id;

  // 0:本地文件 1: s3 2: webdav
  @TableField("storage_type")
  int storageType;

  // 0: image, 1: text, 2: video, 3: audio, 4: other
  @TableField("data_type")
  int dataType;

  @TableField("url")
  String url;

  @TableField("file_name")
  String fileName;

  /** 创建时间 */
  @TableField(value = "created_at")
  private LocalDateTime createdAt;

  /** 更新时间 */
  @TableField(value = "updated_at")
  private LocalDateTime updatedAt;

  /** 是否已删除（逻辑删除） */
  @TableField("is_deleted")
  @JsonIgnore
  private Integer isDeleted;
}
