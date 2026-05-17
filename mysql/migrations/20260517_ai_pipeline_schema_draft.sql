-- AI Pipeline 首期数据库结构草案
-- 适用于已有业务数据的 MySQL 数据库
-- 执行方式：mysql -u <user> -p <db> < mysql/migrations/20260517_ai_pipeline_schema_draft.sql
-- 说明：
-- 1. 本脚本按“同库分表”方案新增 ai_pipeline 相关表
-- 2. 当前作为首期草案，字段与索引在最终确认后可继续微调
-- 3. 执行后请同步更新 mysql/init/01_init_automl.sql

SET NAMES utf8mb4;

DROP PROCEDURE IF EXISTS `automl_apply_ai_pipeline_schema_20260517`;

DELIMITER $$

CREATE PROCEDURE `automl_apply_ai_pipeline_schema_20260517`()
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'annotation'
      AND COLUMN_NAME = 'default_ai_pipeline_binding_id'
  ) THEN
    ALTER TABLE `annotation`
      ADD COLUMN `default_ai_pipeline_binding_id` BIGINT DEFAULT NULL COMMENT '默认 AI Pipeline 绑定ID' AFTER `assist_pipeline`;
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM information_schema.TABLES
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'ai_pipeline_template'
  ) THEN
    CREATE TABLE `ai_pipeline_template` (
      `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
      `template_key` VARCHAR(128) NOT NULL COMMENT '模板稳定标识',
      `name` VARCHAR(255) NOT NULL COMMENT '模板名称',
      `description` TEXT DEFAULT NULL COMMENT '模板描述',
      `scene_type` VARCHAR(64) NOT NULL COMMENT '场景类型',
      `input_kind` VARCHAR(64) DEFAULT NULL COMMENT '主输入类型',
      `output_kind` VARCHAR(64) DEFAULT NULL COMMENT '主输出类型',
      `status` VARCHAR(32) NOT NULL DEFAULT 'draft' COMMENT '状态: draft/published/disabled',
      `latest_version` INT NOT NULL DEFAULT 1 COMMENT '最新版本号',
      `published_version` INT DEFAULT NULL COMMENT '当前发布版本号',
      `is_builtin` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否系统内置模板',
      `created_by` VARCHAR(64) DEFAULT NULL COMMENT '创建人',
      `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
      `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
      `is_deleted` TINYINT(1) DEFAULT 0 COMMENT '逻辑删除标记',
      PRIMARY KEY (`id`),
      UNIQUE KEY `uk_ai_pipeline_template_key` (`template_key`),
      KEY `idx_ai_pipeline_template_scene_type` (`scene_type`),
      KEY `idx_ai_pipeline_template_status` (`status`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='AI Pipeline 模板主表';
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM information_schema.TABLES
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'ai_pipeline_template_version'
  ) THEN
    CREATE TABLE `ai_pipeline_template_version` (
      `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
      `template_id` BIGINT NOT NULL COMMENT '模板ID',
      `version` INT NOT NULL COMMENT '版本号',
      `definition_json` LONGTEXT DEFAULT NULL COMMENT '模板 DSL JSON',
      `form_schema_json` LONGTEXT DEFAULT NULL COMMENT '表单 Schema JSON',
      `change_note` VARCHAR(512) DEFAULT NULL COMMENT '变更说明',
      `is_published` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否已发布',
      `created_by` VARCHAR(64) DEFAULT NULL COMMENT '创建人',
      `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
      `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
      `is_deleted` TINYINT(1) DEFAULT 0 COMMENT '逻辑删除标记',
      PRIMARY KEY (`id`),
      UNIQUE KEY `uk_ai_pipeline_template_version` (`template_id`, `version`),
      KEY `idx_ai_pipeline_template_version_published` (`template_id`, `is_published`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='AI Pipeline 模板版本表';
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM information_schema.TABLES
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'ai_pipeline_binding'
  ) THEN
    CREATE TABLE `ai_pipeline_binding` (
      `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
      `binding_type` VARCHAR(64) NOT NULL COMMENT '绑定对象类型',
      `binding_target_id` BIGINT NOT NULL COMMENT '绑定对象ID',
      `template_id` BIGINT NOT NULL COMMENT '模板ID',
      `template_version` INT NOT NULL COMMENT '模板版本',
      `name` VARCHAR(255) DEFAULT NULL COMMENT '绑定名称',
      `description` TEXT DEFAULT NULL COMMENT '绑定说明',
      `is_default` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否默认绑定',
      `runtime_input_defaults_json` LONGTEXT DEFAULT NULL COMMENT '默认运行参数 JSON',
      `resource_bindings_json` LONGTEXT DEFAULT NULL COMMENT '资源绑定 JSON',
      `created_by` VARCHAR(64) DEFAULT NULL COMMENT '创建人',
      `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
      `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
      `is_deleted` TINYINT(1) DEFAULT 0 COMMENT '逻辑删除标记',
      PRIMARY KEY (`id`),
      KEY `idx_ai_pipeline_binding_target` (`binding_type`, `binding_target_id`),
      KEY `idx_ai_pipeline_binding_template` (`template_id`, `template_version`),
      KEY `idx_ai_pipeline_binding_default` (`binding_type`, `binding_target_id`, `is_default`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='AI Pipeline 业务绑定表';
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM information_schema.TABLES
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'ai_pipeline_run'
  ) THEN
    CREATE TABLE `ai_pipeline_run` (
      `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
      `run_id` VARCHAR(64) NOT NULL COMMENT '外部运行ID',
      `template_id` BIGINT NOT NULL COMMENT '模板ID',
      `template_version` INT NOT NULL COMMENT '模板版本',
      `binding_id` BIGINT DEFAULT NULL COMMENT '绑定ID',
      `source_type` VARCHAR(64) DEFAULT NULL COMMENT '触发来源类型',
      `source_id` BIGINT DEFAULT NULL COMMENT '触发来源ID',
      `trigger_mode` VARCHAR(32) NOT NULL DEFAULT 'sync' COMMENT '触发方式: sync/async',
      `execution_mode` VARCHAR(32) NOT NULL DEFAULT 'interactive' COMMENT '执行模式: interactive/batch/video',
      `status` VARCHAR(32) NOT NULL DEFAULT 'pending' COMMENT '状态: pending/queued/running/succeeded/failed/canceled',
      `progress` INT NOT NULL DEFAULT 0 COMMENT '进度 0-100',
      `data_inputs_json` LONGTEXT DEFAULT NULL COMMENT '数据输入 JSON',
      `runtime_inputs_json` LONGTEXT DEFAULT NULL COMMENT '运行参数 JSON',
      `resource_bindings_json` LONGTEXT DEFAULT NULL COMMENT '执行时资源绑定快照 JSON',
      `result_summary_json` LONGTEXT DEFAULT NULL COMMENT '结果摘要 JSON',
      `error_message` TEXT DEFAULT NULL COMMENT '错误信息',
      `started_at` DATETIME DEFAULT NULL COMMENT '开始时间',
      `finished_at` DATETIME DEFAULT NULL COMMENT '结束时间',
      `created_by` VARCHAR(64) DEFAULT NULL COMMENT '触发人',
      `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
      `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
      `is_deleted` TINYINT(1) DEFAULT 0 COMMENT '逻辑删除标记',
      PRIMARY KEY (`id`),
      UNIQUE KEY `uk_ai_pipeline_run_run_id` (`run_id`),
      KEY `idx_ai_pipeline_run_status` (`status`),
      KEY `idx_ai_pipeline_run_source` (`source_type`, `source_id`),
      KEY `idx_ai_pipeline_run_binding` (`binding_id`),
      KEY `idx_ai_pipeline_run_created_at` (`created_at`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='AI Pipeline 运行主表';
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM information_schema.TABLES
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'ai_pipeline_run_step'
  ) THEN
    CREATE TABLE `ai_pipeline_run_step` (
      `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
      `run_id` BIGINT NOT NULL COMMENT '运行主表ID',
      `step_key` VARCHAR(128) NOT NULL COMMENT '步骤Key',
      `step_name` VARCHAR(255) DEFAULT NULL COMMENT '步骤名称',
      `step_type` VARCHAR(64) DEFAULT NULL COMMENT '步骤类型',
      `executor` VARCHAR(128) DEFAULT NULL COMMENT '执行器名称',
      `status` VARCHAR(32) NOT NULL DEFAULT 'pending' COMMENT '步骤状态',
      `attempt_count` INT NOT NULL DEFAULT 0 COMMENT '尝试次数',
      `input_ref_json` LONGTEXT DEFAULT NULL COMMENT '输入引用 JSON',
      `output_ref_json` LONGTEXT DEFAULT NULL COMMENT '输出引用 JSON',
      `error_message` TEXT DEFAULT NULL COMMENT '错误信息',
      `started_at` DATETIME DEFAULT NULL COMMENT '开始时间',
      `finished_at` DATETIME DEFAULT NULL COMMENT '结束时间',
      `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
      `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
      `is_deleted` TINYINT(1) DEFAULT 0 COMMENT '逻辑删除标记',
      PRIMARY KEY (`id`),
      KEY `idx_ai_pipeline_run_step_run_id` (`run_id`),
      KEY `idx_ai_pipeline_run_step_status` (`run_id`, `status`),
      KEY `idx_ai_pipeline_run_step_key` (`run_id`, `step_key`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='AI Pipeline 步骤运行表';
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM information_schema.TABLES
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'ai_pipeline_artifact'
  ) THEN
    CREATE TABLE `ai_pipeline_artifact` (
      `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
      `run_id` BIGINT NOT NULL COMMENT '运行主表ID',
      `run_step_id` BIGINT DEFAULT NULL COMMENT '步骤运行ID',
      `artifact_key` VARCHAR(128) DEFAULT NULL COMMENT '产物Key',
      `artifact_type` VARCHAR(64) NOT NULL COMMENT '产物类型',
      `storage_type` VARCHAR(32) NOT NULL COMMENT '存储类型',
      `bucket_name` VARCHAR(128) DEFAULT NULL COMMENT 'Bucket名称',
      `object_key` VARCHAR(512) DEFAULT NULL COMMENT '对象路径',
      `content_type` VARCHAR(128) DEFAULT NULL COMMENT '内容类型',
      `size_bytes` BIGINT DEFAULT NULL COMMENT '大小字节数',
      `metadata_json` LONGTEXT DEFAULT NULL COMMENT '扩展元数据 JSON',
      `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
      `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
      `is_deleted` TINYINT(1) DEFAULT 0 COMMENT '逻辑删除标记',
      PRIMARY KEY (`id`),
      KEY `idx_ai_pipeline_artifact_run_id` (`run_id`),
      KEY `idx_ai_pipeline_artifact_run_step_id` (`run_step_id`),
      KEY `idx_ai_pipeline_artifact_type` (`artifact_type`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='AI Pipeline 产物索引表';
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM information_schema.TABLES
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'ai_pipeline_event_log'
  ) THEN
    CREATE TABLE `ai_pipeline_event_log` (
      `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
      `run_id` BIGINT NOT NULL COMMENT '运行主表ID',
      `event_type` VARCHAR(64) NOT NULL COMMENT '事件类型',
      `event_payload` LONGTEXT DEFAULT NULL COMMENT '事件内容 JSON',
      `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
      `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
      `is_deleted` TINYINT(1) DEFAULT 0 COMMENT '逻辑删除标记',
      PRIMARY KEY (`id`),
      KEY `idx_ai_pipeline_event_log_run_id` (`run_id`, `created_at`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='AI Pipeline 事件日志表';
  END IF;
END $$

DELIMITER ;

CALL `automl_apply_ai_pipeline_schema_20260517`();
DROP PROCEDURE IF EXISTS `automl_apply_ai_pipeline_schema_20260517`;

SELECT 'AI Pipeline schema draft applied.' AS message;
