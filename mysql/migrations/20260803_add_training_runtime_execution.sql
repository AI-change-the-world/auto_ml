-- Apply after 20260803_add_training_runtime_catalog.sql on existing databases.
-- Package releases created before input modes were introduced retain the
-- backwards-compatible platform_dataset default.

SET @training_runtime_input_modes_migration = (
  SELECT IF(
    COUNT(*) = 0,
    'ALTER TABLE `training_runtime_code_package` ADD COLUMN `input_modes_json` LONGTEXT NOT NULL DEFAULT (''["platform_dataset"]'') COMMENT ''训练数据输入模式 JSON'' AFTER `supported_tasks_json`',
    'SELECT 1'
  )
  FROM information_schema.columns
  WHERE table_schema = DATABASE()
    AND table_name = 'training_runtime_code_package'
    AND column_name = 'input_modes_json'
);
PREPARE training_runtime_input_modes_statement FROM @training_runtime_input_modes_migration;
EXECUTE training_runtime_input_modes_statement;
DEALLOCATE PREPARE training_runtime_input_modes_statement;

CREATE TABLE IF NOT EXISTS `training_runtime_execution` (
  `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `is_deleted` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '逻辑删除标记',
  `task_id` BIGINT NOT NULL COMMENT '平台训练任务ID',
  `execution_id` CHAR(36) NOT NULL COMMENT '不可变运行执行ID',
  `code_package_id` BIGINT NOT NULL COMMENT '训练脚本包ID',
  `model_package_id` BIGINT DEFAULT NULL COMMENT '可选输入模型包ID',
  `input_mode` VARCHAR(32) NOT NULL COMMENT 'platform_dataset/script_managed',
  `submission_json` LONGTEXT NOT NULL COMMENT 'training-code-submit/v1 快照',
  `status` VARCHAR(32) NOT NULL DEFAULT 'queued' COMMENT 'queued/running/succeeded/failed',
  `result_json` LONGTEXT DEFAULT NULL COMMENT 'training-result/v1 与产物摘要',
  `error_message` TEXT DEFAULT NULL COMMENT '执行错误',
  `model_registered` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '可部署模型是否已登记',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_training_runtime_execution_task` (`task_id`),
  UNIQUE KEY `uk_training_runtime_execution_execution_id` (`execution_id`),
  KEY `idx_training_runtime_execution_status` (`status`, `created_at`),
  KEY `idx_training_runtime_execution_code_package` (`code_package_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='自定义训练脚本执行记录';
