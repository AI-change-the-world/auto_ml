package org.xiaoshuyui.automl.module.predict.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;

import org.xiaoshuyui.automl.module.BaseEntity;

import lombok.Data;
import lombok.EqualsAndHashCode;

@Data
@EqualsAndHashCode(callSuper = false)
@TableName(value = "predict_data", autoResultMap = true)
public class PredictData extends BaseEntity {
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

}
