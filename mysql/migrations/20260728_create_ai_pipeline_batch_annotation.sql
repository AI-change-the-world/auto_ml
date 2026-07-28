-- Batch annotation sandbox task tables.
-- Apply this migration to existing AutoML databases before deploying the sandbox.

CREATE TABLE IF NOT EXISTS `ai_pipeline_batch_run` (
  `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `is_deleted` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '逻辑删除标记',
  `run_id` VARCHAR(64) NOT NULL COMMENT '外部运行ID',
  `dataset_id` BIGINT NOT NULL COMMENT '数据集ID',
  `annotation_id` BIGINT NOT NULL COMMENT '标注项目ID',
  `script_key` VARCHAR(128) NOT NULL COMMENT '内置脚本标识',
  `script_version` VARCHAR(64) NOT NULL COMMENT '脚本版本',
  `status` VARCHAR(32) NOT NULL DEFAULT 'queued' COMMENT 'queued/running/succeeded/failed/canceled',
  `selection_mode` VARCHAR(32) NOT NULL DEFAULT 'all' COMMENT 'all/unannotated/selected',
  `overwrite_policy` VARCHAR(32) NOT NULL DEFAULT 'skip_existing' COMMENT '覆盖策略',
  `batch_size` INT NOT NULL DEFAULT 20 COMMENT '单次脚本输入样本数',
  `parallelism` INT NOT NULL DEFAULT 1 COMMENT '并发批次数',
  `total_count` INT NOT NULL DEFAULT 0 COMMENT '总样本数',
  `succeeded_count` INT NOT NULL DEFAULT 0 COMMENT '成功数',
  `failed_count` INT NOT NULL DEFAULT 0 COMMENT '失败数',
  `skipped_count` INT NOT NULL DEFAULT 0 COMMENT '跳过数',
  `canceled_count` INT NOT NULL DEFAULT 0 COMMENT '取消数',
  `progress` INT NOT NULL DEFAULT 0 COMMENT '进度 0-100',
  `cancel_requested` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '取消标记',
  `script_params_json` LONGTEXT DEFAULT NULL COMMENT '脚本参数快照 JSON',
  `annotation_snapshot_json` LONGTEXT DEFAULT NULL COMMENT '标注配置快照 JSON',
  `error_message` TEXT DEFAULT NULL COMMENT '任务错误',
  `started_at` DATETIME DEFAULT NULL COMMENT '开始时间',
  `finished_at` DATETIME DEFAULT NULL COMMENT '结束时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_ai_pipeline_batch_run_run_id` (`run_id`),
  KEY `idx_ai_pipeline_batch_run_dataset` (`dataset_id`, `created_at`),
  KEY `idx_ai_pipeline_batch_run_annotation` (`annotation_id`, `created_at`),
  KEY `idx_ai_pipeline_batch_run_status` (`status`, `created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='AI Pipeline 批量标注任务';

CREATE TABLE IF NOT EXISTS `ai_pipeline_batch_run_item` (
  `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `is_deleted` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '逻辑删除标记',
  `batch_run_id` BIGINT NOT NULL COMMENT '批量任务主表ID',
  `sample_item_id` BIGINT NOT NULL COMMENT '样本ID',
  `item_key` VARCHAR(255) NOT NULL COMMENT '样本业务键快照',
  `asset_path` VARCHAR(512) DEFAULT NULL COMMENT '数据集对象路径快照',
  `asset_mime_type` VARCHAR(128) DEFAULT NULL COMMENT '资源 MIME 快照',
  `input_snapshot_json` LONGTEXT DEFAULT NULL COMMENT '脚本输入快照 JSON',
  `chunk_key` VARCHAR(96) DEFAULT NULL COMMENT 'MQ 批次标识',
  `status` VARCHAR(32) NOT NULL DEFAULT 'pending' COMMENT 'pending/queued/succeeded/failed/skipped/canceled',
  `attempt_count` INT NOT NULL DEFAULT 0 COMMENT '派发次数',
  `annotation_record_id` BIGINT DEFAULT NULL COMMENT '写入后的标注记录ID',
  `result_json` LONGTEXT DEFAULT NULL COMMENT '脚本结果快照 JSON',
  `error_message` TEXT DEFAULT NULL COMMENT '错误信息',
  `started_at` DATETIME DEFAULT NULL COMMENT '开始时间',
  `finished_at` DATETIME DEFAULT NULL COMMENT '结束时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_ai_pipeline_batch_run_item_sample` (`batch_run_id`, `sample_item_id`),
  KEY `idx_ai_pipeline_batch_run_item_status` (`batch_run_id`, `status`),
  KEY `idx_ai_pipeline_batch_run_item_chunk` (`chunk_key`),
  KEY `idx_ai_pipeline_batch_run_item_annotation_record` (`annotation_record_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='AI Pipeline 批量标注任务样本';

CREATE TABLE IF NOT EXISTS `ai_pipeline_batch_run_event` (
  `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `is_deleted` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '逻辑删除标记',
  `batch_run_id` BIGINT NOT NULL COMMENT '批量任务主表ID',
  `event_type` VARCHAR(64) NOT NULL COMMENT 'queued/progress/result/failed/canceled',
  `event_payload` LONGTEXT DEFAULT NULL COMMENT '事件内容 JSON',
  PRIMARY KEY (`id`),
  KEY `idx_ai_pipeline_batch_run_event_run` (`batch_run_id`, `id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='AI Pipeline 批量标注任务事件';
