-- User-managed ZIP script packages for the batch annotation sandbox.
-- Apply after 20260728_create_ai_pipeline_batch_annotation.sql.

CREATE TABLE IF NOT EXISTS `ai_pipeline_batch_script` (
  `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `is_deleted` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '逻辑删除标记',
  `script_key` VARCHAR(128) NOT NULL COMMENT '脚本标识',
  `version` VARCHAR(64) NOT NULL COMMENT '脚本版本',
  `name` VARCHAR(255) NOT NULL COMMENT '脚本名称',
  `description` TEXT DEFAULT NULL COMMENT '脚本描述',
  `package_object_key` VARCHAR(512) NOT NULL COMMENT 'ZIP 脚本包对象路径',
  `package_file_name` VARCHAR(255) NOT NULL COMMENT '上传文件名',
  `entrypoint` VARCHAR(255) NOT NULL COMMENT 'ZIP 内 Python 入口文件',
  `supported_data_types_json` TEXT NOT NULL COMMENT '兼容数据类型 JSON',
  `supported_annotation_types_json` TEXT NOT NULL COMMENT '兼容标注类型 JSON',
  `parameter_fields_json` LONGTEXT NOT NULL COMMENT '运行参数 Schema JSON',
  `enabled` TINYINT(1) NOT NULL DEFAULT 1 COMMENT '是否允许创建新任务',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_ai_pipeline_batch_script_key` (`script_key`),
  KEY `idx_ai_pipeline_batch_script_enabled` (`enabled`, `created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='AI Pipeline 批量标注脚本包';

ALTER TABLE `ai_pipeline_batch_run`
  ADD COLUMN `script_package_path` VARCHAR(512) DEFAULT NULL COMMENT '脚本包对象路径快照' AFTER `script_version`,
  ADD COLUMN `script_entrypoint` VARCHAR(255) DEFAULT NULL COMMENT '脚本入口文件快照' AFTER `script_package_path`;
