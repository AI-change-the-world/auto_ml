package org.xiaoshuyui.automl.module.dataset.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

@TableName("dataset_storage")
@Data
public class DatasetStorage {
    @TableId(value = "dataset_id", type = IdType.AUTO)
    Long id;
    @TableField("storage_type")
    int storageType;
    @TableField("url")
    String url;
    @TableField("username")
    String username;
    @TableField("password")
    String password;

    /// 0: scanning, 1: scan success, 2: scan failed
    @TableField("scan_status")
    int scanStatus;
    @TableField("updated_at")
    LocalDateTime updatedAt;
}
