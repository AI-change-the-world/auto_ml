-- Auto ML 手动数据库升级脚本
-- 适用于已经有业务数据的 MySQL 数据库
-- 执行方式：mysql -u <user> -p <db> < mysql/migrations/20260510_manual_schema_sync.sql
-- 说明：执行后请保持 mysql/init/01_init_automl.sql 与当前结构同步

SET NAMES utf8mb4;

DROP PROCEDURE IF EXISTS `automl_apply_schema_sync_20260510`;

DELIMITER $$

CREATE PROCEDURE `automl_apply_schema_sync_20260510`()
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'available_model'
      AND COLUMN_NAME = 'onnx_model_path'
  ) THEN
    ALTER TABLE `available_model`
      ADD COLUMN `onnx_model_path` VARCHAR(512) DEFAULT NULL COMMENT 'ONNX模型路径' AFTER `model_path`;
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'available_model'
      AND COLUMN_NAME = 'class_names'
  ) THEN
    ALTER TABLE `available_model`
      ADD COLUMN `class_names` TEXT DEFAULT NULL COMMENT '类别名称 JSON' AFTER `model_type`;
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'available_model'
      AND COLUMN_NAME = 'deployed_at'
  ) THEN
    ALTER TABLE `available_model`
      ADD COLUMN `deployed_at` DATETIME DEFAULT NULL COMMENT '最近一次部署时间' AFTER `deployment_device`;
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'available_model'
      AND COLUMN_NAME = 'inference_count'
  ) THEN
    ALTER TABLE `available_model`
      ADD COLUMN `inference_count` BIGINT NOT NULL DEFAULT 0 COMMENT '累计推理调用次数' AFTER `deployed_at`;
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'available_model'
      AND COLUMN_NAME = 'last_inference_at'
  ) THEN
    ALTER TABLE `available_model`
      ADD COLUMN `last_inference_at` DATETIME DEFAULT NULL COMMENT '最近一次推理时间' AFTER `inference_count`;
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'dataset'
      AND COLUMN_NAME = 'scenario_type'
  ) THEN
    ALTER TABLE `dataset`
      ADD COLUMN `scenario_type` INT DEFAULT 0 COMMENT '场景类型: 0=普通, 1=无人机航拍/拼接, 2=LLM对话标注, 3=MLLM对话标注, 4=DPO兼容, 5=DPO二选一, 6=DPO多选一, 7=DPO参考增强, 8=DPO多轮对话' AFTER `data_type`;
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'dataset'
      AND COLUMN_NAME = 'scenario_config'
  ) THEN
    ALTER TABLE `dataset`
      ADD COLUMN `scenario_config` TEXT DEFAULT NULL COMMENT '场景配置 JSON' AFTER `scenario_type`;
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'annotation'
      AND COLUMN_NAME = 'assist_pipeline'
  ) THEN
    ALTER TABLE `annotation`
      ADD COLUMN `assist_pipeline` VARCHAR(128) DEFAULT NULL COMMENT '默认辅助标注 Pipeline' AFTER `prompt`;
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM information_schema.TABLES
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'task_source'
  ) THEN
    CREATE TABLE `task_source` (
      `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
      `task_id` BIGINT NOT NULL COMMENT '任务ID',
      `dataset_id` BIGINT NOT NULL COMMENT '数据集ID',
      `annotation_id` BIGINT NOT NULL COMMENT '标注ID',
      `source_order` INT DEFAULT 0 COMMENT '来源顺序',
      `source_name` VARCHAR(255) DEFAULT NULL COMMENT '来源名称快照',
      `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
      `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
      `is_deleted` TINYINT(1) DEFAULT 0 COMMENT '逻辑删除标记',
      PRIMARY KEY (`id`),
      KEY `idx_task_source_task_id` (`task_id`),
      KEY `idx_task_source_dataset_id` (`dataset_id`),
      KEY `idx_task_source_annotation_id` (`annotation_id`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='任务训练数据源';
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM information_schema.TABLES
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'model_inference_log'
  ) THEN
    CREATE TABLE `model_inference_log` (
      `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
      `model_id` BIGINT NOT NULL COMMENT '模型ID',
      `request_type` VARCHAR(32) DEFAULT NULL COMMENT '请求方式: file/base64',
      `success` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否成功',
      `duration_ms` INT DEFAULT NULL COMMENT '推理耗时毫秒',
      `result_count` INT NOT NULL DEFAULT 0 COMMENT '返回结果数量',
      `image_width` INT DEFAULT NULL COMMENT '图像宽度',
      `image_height` INT DEFAULT NULL COMMENT '图像高度',
      `error_message` TEXT DEFAULT NULL COMMENT '错误信息',
      `client_ip` VARCHAR(64) DEFAULT NULL COMMENT '客户端IP',
      `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
      `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
      `is_deleted` TINYINT(1) DEFAULT 0 COMMENT '逻辑删除标记',
      PRIMARY KEY (`id`),
      KEY `idx_model_inference_log_model_id` (`model_id`),
      KEY `idx_model_inference_log_created_at` (`created_at`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='模型推理调用记录';
  END IF;

  ALTER TABLE `annotation`
    MODIFY COLUMN `annotation_type` INT DEFAULT 0 COMMENT '标注类型: 0=检测(BBox/OBB), 1=分类, 2=分割(Polygon), 3=MLLM, 4=姿态, 5=LLM, 6=DPO兼容, 7=DPO二选一, 8=DPO多选一, 9=DPO参考增强, 10=DPO多轮对话';

  ALTER TABLE `task`
    MODIFY COLUMN `task_type` INT DEFAULT 0 COMMENT '任务类型: 0=检测, 1=分类, 2=分割, 3=姿态';

  UPDATE `available_model` am
  JOIN `task` t ON am.`task_id` = t.`id` AND t.`is_deleted` = 0
  JOIN `annotation` a ON t.`annotation_id` = a.`id` AND a.`is_deleted` = 0
  SET am.`class_names` = a.`classes`
  WHERE (am.`class_names` IS NULL OR am.`class_names` = '')
    AND a.`classes` IS NOT NULL
    AND a.`classes` <> '';

  INSERT IGNORE INTO `base_models` (`name`, `model_type`, `description`, `save_path`)
  VALUES
    ('yolov8n.pt', 'detection', 'YOLOv8 nano detection baseline', 'yolov8n.pt'),
    ('yolov8s.pt', 'detection', 'YOLOv8 small detection baseline', 'yolov8s.pt'),
    ('yolov8m.pt', 'detection', 'YOLOv8 medium detection baseline', 'yolov8m.pt'),
    ('yolov8l.pt', 'detection', 'YOLOv8 large detection baseline', 'yolov8l.pt'),
    ('yolov8x.pt', 'detection', 'YOLOv8 extra-large detection baseline', 'yolov8x.pt'),
    ('yolov8n-obb.pt', 'detection_obb', 'YOLOv8 nano OBB detection baseline', 'yolov8n-obb.pt'),
    ('yolov8s-obb.pt', 'detection_obb', 'YOLOv8 small OBB detection baseline', 'yolov8s-obb.pt'),
    ('yolov8m-obb.pt', 'detection_obb', 'YOLOv8 medium OBB detection baseline', 'yolov8m-obb.pt'),
    ('yolov8l-obb.pt', 'detection_obb', 'YOLOv8 large OBB detection baseline', 'yolov8l-obb.pt'),
    ('yolov8x-obb.pt', 'detection_obb', 'YOLOv8 extra-large OBB detection baseline', 'yolov8x-obb.pt'),
    ('yolo11n.pt', 'detection', 'YOLO11 nano detection baseline', 'yolo11n.pt'),
    ('yolo11s.pt', 'detection', 'YOLO11 small detection baseline', 'yolo11s.pt'),
    ('yolo11m.pt', 'detection', 'YOLO11 medium detection baseline', 'yolo11m.pt'),
    ('yolo11l.pt', 'detection', 'YOLO11 large detection baseline', 'yolo11l.pt'),
    ('yolo11x.pt', 'detection', 'YOLO11 extra-large detection baseline', 'yolo11x.pt'),
    ('yolo11n-obb.pt', 'detection_obb', 'YOLO11 nano OBB detection baseline', 'yolo11n-obb.pt'),
    ('yolo11s-obb.pt', 'detection_obb', 'YOLO11 small OBB detection baseline', 'yolo11s-obb.pt'),
    ('yolo11m-obb.pt', 'detection_obb', 'YOLO11 medium OBB detection baseline', 'yolo11m-obb.pt'),
    ('yolo11l-obb.pt', 'detection_obb', 'YOLO11 large OBB detection baseline', 'yolo11l-obb.pt'),
    ('yolo11x-obb.pt', 'detection_obb', 'YOLO11 extra-large OBB detection baseline', 'yolo11x-obb.pt'),
    ('yolov8n-cls.pt', 'classification', 'YOLOv8 nano classification baseline', 'yolov8n-cls.pt'),
    ('yolov8s-cls.pt', 'classification', 'YOLOv8 small classification baseline', 'yolov8s-cls.pt'),
    ('yolov8m-cls.pt', 'classification', 'YOLOv8 medium classification baseline', 'yolov8m-cls.pt'),
    ('yolov8l-cls.pt', 'classification', 'YOLOv8 large classification baseline', 'yolov8l-cls.pt'),
    ('yolov8x-cls.pt', 'classification', 'YOLOv8 extra-large classification baseline', 'yolov8x-cls.pt'),
    ('yolo11n-cls.pt', 'classification', 'YOLO11 nano classification baseline', 'yolo11n-cls.pt'),
    ('yolo11s-cls.pt', 'classification', 'YOLO11 small classification baseline', 'yolo11s-cls.pt'),
    ('yolo11m-cls.pt', 'classification', 'YOLO11 medium classification baseline', 'yolo11m-cls.pt'),
    ('yolo11l-cls.pt', 'classification', 'YOLO11 large classification baseline', 'yolo11l-cls.pt'),
    ('yolo11x-cls.pt', 'classification', 'YOLO11 extra-large classification baseline', 'yolo11x-cls.pt'),
    ('yolov8n-seg.pt', 'segmentation', 'YOLOv8 nano segmentation baseline', 'yolov8n-seg.pt'),
    ('yolov8s-seg.pt', 'segmentation', 'YOLOv8 small segmentation baseline', 'yolov8s-seg.pt'),
    ('yolov8m-seg.pt', 'segmentation', 'YOLOv8 medium segmentation baseline', 'yolov8m-seg.pt'),
    ('yolov8l-seg.pt', 'segmentation', 'YOLOv8 large segmentation baseline', 'yolov8l-seg.pt'),
    ('yolov8x-seg.pt', 'segmentation', 'YOLOv8 extra-large segmentation baseline', 'yolov8x-seg.pt'),
    ('yolo11n-seg.pt', 'segmentation', 'YOLO11 nano segmentation baseline', 'yolo11n-seg.pt'),
    ('yolo11s-seg.pt', 'segmentation', 'YOLO11 small segmentation baseline', 'yolo11s-seg.pt'),
    ('yolo11m-seg.pt', 'segmentation', 'YOLO11 medium segmentation baseline', 'yolo11m-seg.pt'),
    ('yolo11l-seg.pt', 'segmentation', 'YOLO11 large segmentation baseline', 'yolo11l-seg.pt'),
    ('yolo11x-seg.pt', 'segmentation', 'YOLO11 extra-large segmentation baseline', 'yolo11x-seg.pt');
END $$

DELIMITER ;

CALL `automl_apply_schema_sync_20260510`();
DROP PROCEDURE IF EXISTS `automl_apply_schema_sync_20260510`;

SELECT 'Auto ML manual schema sync completed.' AS message;
