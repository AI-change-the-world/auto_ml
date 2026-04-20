-- Auto ML 数据库初始化脚本
-- 对齐 automl_server 当前 SQLAlchemy 模型

SET NAMES utf8mb4;

CREATE TABLE IF NOT EXISTS `dataset` (
  `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `name` VARCHAR(255) NOT NULL COMMENT '数据集名称',
  `storage_type` INT DEFAULT 1 COMMENT '存储类型: 0=本地, 1=S3, 2=WebDAV',
  `data_type` INT DEFAULT 0 COMMENT '数据类型: 0=图像, 1=文本, 2=视频, 3=音频',
  `scenario_type` INT DEFAULT 0 COMMENT '场景类型: 0=普通, 1=无人机航拍/拼接',
  `scenario_config` TEXT COMMENT '场景配置 JSON',
  `save_path` VARCHAR(512) DEFAULT NULL COMMENT '存储路径',
  `count` INT DEFAULT 0 COMMENT '文件数量',
  `description` TEXT COMMENT '描述',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `is_deleted` TINYINT(1) DEFAULT 0 COMMENT '逻辑删除标记',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='数据集';

CREATE TABLE IF NOT EXISTS `dataset_file` (
  `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `dataset_id` BIGINT NOT NULL COMMENT '数据集ID',
  `file_name` VARCHAR(255) NOT NULL COMMENT '文件名',
  `save_path` VARCHAR(512) DEFAULT NULL COMMENT '存储路径',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `is_deleted` TINYINT(1) DEFAULT 0 COMMENT '逻辑删除标记',
  PRIMARY KEY (`id`),
  KEY `idx_dataset_file_dataset_id` (`dataset_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='数据集文件';

CREATE TABLE IF NOT EXISTS `annotation` (
  `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `name` VARCHAR(255) NOT NULL COMMENT '标注项目名称',
  `annotation_type` INT DEFAULT 0 COMMENT '标注类型: 0=检测(BBox/OBB), 1=分类, 2=分割(Polygon), 3=MLLM',
  `classes` TEXT COMMENT '分类项 JSON',
  `storage_type` INT DEFAULT 1 COMMENT '存储类型: 0=本地, 1=S3, 2=WebDAV',
  `save_path` VARCHAR(512) DEFAULT NULL COMMENT '存储路径',
  `prompt` TEXT COMMENT 'AI 标注提示词',
  `dataset_id` BIGINT DEFAULT NULL COMMENT '关联数据集ID',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `is_deleted` TINYINT(1) DEFAULT 0 COMMENT '逻辑删除标记',
  PRIMARY KEY (`id`),
  KEY `idx_annotation_dataset_id` (`dataset_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='标注项目';

CREATE TABLE IF NOT EXISTS `annotation_file` (
  `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `annotation_id` BIGINT NOT NULL COMMENT '标注项目ID',
  `file_name` VARCHAR(255) NOT NULL COMMENT '文件名',
  `save_path` VARCHAR(512) DEFAULT NULL COMMENT '存储路径',
  `content` TEXT COMMENT '标注内容',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `is_deleted` TINYINT(1) DEFAULT 0 COMMENT '逻辑删除标记',
  PRIMARY KEY (`id`),
  KEY `idx_annotation_file_annotation_id` (`annotation_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='标注文件';

CREATE TABLE IF NOT EXISTS `task` (
  `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `task_type` INT DEFAULT 0 COMMENT '任务类型: 0=检测, 1=分类',
  `dataset_id` BIGINT DEFAULT NULL COMMENT '数据集ID',
  `annotation_id` BIGINT DEFAULT NULL COMMENT '标注ID',
  `status` INT DEFAULT 0 COMMENT '状态: 0=待处理, 1=运行中, 2=后处理, 3=完成, 4=失败',
  `config` TEXT COMMENT '配置 JSON',
  `result` TEXT COMMENT '结果 JSON',
  `error_message` TEXT COMMENT '错误信息',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `is_deleted` TINYINT(1) DEFAULT 0 COMMENT '逻辑删除标记',
  PRIMARY KEY (`id`),
  KEY `idx_task_dataset_id` (`dataset_id`),
  KEY `idx_task_annotation_id` (`annotation_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='训练任务';

CREATE TABLE IF NOT EXISTS `task_log` (
  `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `task_id` BIGINT NOT NULL COMMENT '任务ID',
  `content` TEXT COMMENT '日志内容',
  `log_level` VARCHAR(20) DEFAULT 'INFO' COMMENT '日志级别',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `is_deleted` TINYINT(1) DEFAULT 0 COMMENT '逻辑删除标记',
  PRIMARY KEY (`id`),
  KEY `idx_task_log_task_id` (`task_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='任务日志';

CREATE TABLE IF NOT EXISTS `task_source` (
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

CREATE TABLE IF NOT EXISTS `base_models` (
  `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `name` VARCHAR(255) NOT NULL COMMENT '模型名称',
  `model_type` VARCHAR(50) DEFAULT NULL COMMENT '模型类型',
  `description` TEXT COMMENT '描述',
  `save_path` VARCHAR(512) DEFAULT NULL COMMENT '模型路径',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `is_deleted` TINYINT(1) DEFAULT 0 COMMENT '逻辑删除标记',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_base_models_name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='基础模型';

CREATE TABLE IF NOT EXISTS `available_model` (
  `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `name` VARCHAR(255) DEFAULT NULL COMMENT '模型名称',
  `model_path` VARCHAR(512) DEFAULT NULL COMMENT '模型路径',
  `onnx_model_path` VARCHAR(512) DEFAULT NULL COMMENT 'ONNX模型路径',
  `model_type` VARCHAR(50) DEFAULT NULL COMMENT '模型类型',
  `dataset_id` BIGINT DEFAULT NULL COMMENT '关联数据集ID',
  `task_id` BIGINT DEFAULT NULL COMMENT '关联任务ID',
  `loss` FLOAT DEFAULT NULL COMMENT '训练损失',
  `is_deployed` TINYINT(1) DEFAULT 0 COMMENT '是否已部署',
  `deployment_id` VARCHAR(100) DEFAULT NULL COMMENT '部署ID',
  `deployment_port` INT DEFAULT NULL COMMENT '部署端口',
  `deployment_version` VARCHAR(50) DEFAULT NULL COMMENT '部署版本',
  `deployment_device` VARCHAR(50) DEFAULT NULL COMMENT '部署设备',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `is_deleted` TINYINT(1) DEFAULT 0 COMMENT '逻辑删除标记',
  PRIMARY KEY (`id`),
  KEY `idx_available_model_dataset_id` (`dataset_id`),
  KEY `idx_available_model_task_id` (`task_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='可用模型';

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
  ('yolo11x-cls.pt', 'classification', 'YOLO11 extra-large classification baseline', 'yolo11x-cls.pt');

SELECT 'Auto ML database initialized successfully!' AS message;
