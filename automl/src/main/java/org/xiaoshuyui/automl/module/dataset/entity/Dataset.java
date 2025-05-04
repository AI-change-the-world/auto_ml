package org.xiaoshuyui.automl.module.dataset.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import com.fasterxml.jackson.annotation.JsonIgnore;
import java.time.LocalDateTime;
import lombok.Data;

@Data
@TableName("dataset")
public class Dataset {

  @TableId(value = "dataset_id", type = IdType.AUTO)
  private Long id;

  @TableField("dataset_name")
  private String name;

  @TableField("description")
  private String description;

  @TableField("created_at")
  private LocalDateTime createdAt;

  @TableField("updated_at")
  private LocalDateTime updatedAt;

  @JsonIgnore
  @TableField("is_deleted")
  private Integer isDeleted;

  // 0: image, 1: text, 2: video, 3: audio, 4: other
  @TableField("dataset_type")
  private int type;

  @TableField("ranking")
  private double ranking;

  /*
   * 2025-05-03,打算除本来就在对象存储的所有数据，都保存到本地对象存储上
   */
  @TableField("storage_type")
  private Integer storageType;

  @TableField("url")
  private String url;

  @TableField("username")
  private String username;

  @TableField("password")
  private String password;

  // 0: scanning, 1: scan success, 2: scan failed
  @TableField("scan_status")
  private Integer scanStatus;

  @TableField("file_count")
  Long fileCount;

  @TableField("sample_file_path")
  String sampleFilePath;

  // since 2025-05-03
  // 本地对象存储路径
  @TableField("local_s3_storage_path")
  String localS3StoragePath;
}
