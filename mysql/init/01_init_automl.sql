-- Auto ML 数据库初始化脚本

-- 创建 task 表
CREATE TABLE IF NOT EXISTS `task` (
    `task_id` INT AUTO_INCREMENT PRIMARY KEY COMMENT 'task id',
    `task_type` VARCHAR(50) DEFAULT '' COMMENT '0 train; 1 eval; 2 others',
    `dataset_id` INT DEFAULT NULL COMMENT 'dataset id',
    `annotation_id` INT DEFAULT NULL COMMENT 'annotation id',
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    `is_deleted` TINYINT DEFAULT 0 COMMENT '逻辑删除标记',
    `status` TINYINT DEFAULT 0 COMMENT '任务状态, 0 pre task, 1 on task, 2 post task, 3 done, 4 error',
    `task_config` TEXT COMMENT '任务配置JSON'
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '任务表';

-- 创建 task_log 表
CREATE TABLE IF NOT EXISTS `task_log` (
    `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT 'log id',
    `task_id` INT NOT NULL COMMENT 'task id',
    `log_content` VARCHAR(1024) DEFAULT NULL COMMENT '日志内容',
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX `idx_task_id` (`task_id`)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '任务日志表';

-- 创建 available_models 表
CREATE TABLE IF NOT EXISTS `available_models` (
    `available_model_id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键 ID',
    `save_path` VARCHAR(500) DEFAULT NULL COMMENT '保存路径',
    `base_model_name` VARCHAR(200) DEFAULT NULL COMMENT '基础模型名',
    `loss` FLOAT DEFAULT NULL COMMENT 'loss 值',
    `epoch` INT DEFAULT NULL COMMENT '训练轮数',
    `dataset_id` INT DEFAULT NULL COMMENT '数据集 ID',
    `annotation_id` INT DEFAULT NULL COMMENT '标注 ID',
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    `is_deleted` TINYINT DEFAULT 0 COMMENT '逻辑删除标志',
    `model_type` VARCHAR(50) DEFAULT 'detection' COMMENT '模型类型'
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '可用模型表';

-- 创建 deployments 表
CREATE TABLE IF NOT EXISTS `deployments` (
    `deployment_id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '部署ID',
    `model_id` INT NOT NULL COMMENT '模型ID',
    `model_name` VARCHAR(200) DEFAULT NULL COMMENT '模型名称',
    `version` VARCHAR(50) DEFAULT 'v1' COMMENT '版本',
    `status` TINYINT DEFAULT 0 COMMENT '状态: 0-pending, 1-running, 2-stopped, 3-error',
    `port` INT DEFAULT NULL COMMENT '服务端口号',
    `pid` INT DEFAULT NULL COMMENT '进程ID',
    `replicas` INT DEFAULT 1 COMMENT '实例数',
    `device` VARCHAR(50) DEFAULT 'cpu' COMMENT '运行设备',
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX `idx_model_id` (`model_id`),
    INDEX `idx_status` (`status`)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '模型部署记录表';

-- 创建 datasets 表（如果需要）
CREATE TABLE IF NOT EXISTS `datasets` (
    `dataset_id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '数据集 ID',
    `dataset_name` VARCHAR(200) NOT NULL COMMENT '数据集名称',
    `dataset_path` VARCHAR(500) DEFAULT NULL COMMENT '数据集路径',
    `dataset_type` VARCHAR(50) DEFAULT NULL COMMENT '数据集类型',
    `total_count` INT DEFAULT 0 COMMENT '总数量',
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    `is_deleted` TINYINT DEFAULT 0 COMMENT '逻辑删除标志'
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '数据集表';

-- 创建 annotations 表（如果需要）
CREATE TABLE IF NOT EXISTS `annotations` (
    `annotation_id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '标注 ID',
    `dataset_id` INT NOT NULL COMMENT '关联数据集 ID',
    `annotation_name` VARCHAR(200) NOT NULL COMMENT '标注名称',
    `annotation_path` VARCHAR(500) DEFAULT NULL COMMENT '标注文件路径',
    `annotation_type` VARCHAR(50) DEFAULT NULL COMMENT '标注类型',
    `total_count` INT DEFAULT 0 COMMENT '标注数量',
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    `is_deleted` TINYINT DEFAULT 0 COMMENT '逻辑删除标志',
    INDEX `idx_dataset_id` (`dataset_id`)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '标注表';

-- 初始化完成提示
SELECT 'Auto ML database initialized successfully!' AS message;