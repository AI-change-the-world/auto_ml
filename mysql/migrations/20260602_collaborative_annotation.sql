-- Collaborative annotation MVP.
-- Adds anonymous collaborators and sample-level exclusive assignments.

SET NAMES utf8mb4;

CREATE TABLE IF NOT EXISTS `annotation_collaborator` (
  `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `annotation_id` BIGINT NOT NULL COMMENT '标注项目ID',
  `display_name` VARCHAR(64) NOT NULL COMMENT '协作者显示名称',
  `token` VARCHAR(128) NOT NULL COMMENT '协作者访问令牌',
  `status` VARCHAR(32) DEFAULT 'active' COMMENT '状态: active/disabled',
  `last_active_at` DATETIME DEFAULT NULL COMMENT '最近活跃时间',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `is_deleted` TINYINT(1) DEFAULT 0 COMMENT '逻辑删除标记',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_annotation_collaborator_token` (`token`),
  KEY `idx_annotation_collaborator_annotation_id` (`annotation_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='标注协作者';

CREATE TABLE IF NOT EXISTS `annotation_sample_assignment` (
  `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `annotation_id` BIGINT NOT NULL COMMENT '标注项目ID',
  `sample_item_id` BIGINT NOT NULL COMMENT '样本ID',
  `collaborator_id` BIGINT NOT NULL COMMENT '协作者ID',
  `status` VARCHAR(32) DEFAULT 'assigned' COMMENT '状态: assigned/in_progress/submitted/released',
  `lease_expires_at` DATETIME DEFAULT NULL COMMENT '分配锁过期时间',
  `submitted_at` DATETIME DEFAULT NULL COMMENT '提交时间',
  `collab_state` LONGTEXT DEFAULT NULL COMMENT 'Yjs 协作文档快照',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `is_deleted` TINYINT(1) DEFAULT 0 COMMENT '逻辑删除标记',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_annotation_assignment_sample` (`annotation_id`, `sample_item_id`),
  KEY `idx_annotation_sample_assignment_annotation_id` (`annotation_id`),
  KEY `idx_annotation_sample_assignment_sample_item_id` (`sample_item_id`),
  KEY `idx_annotation_sample_assignment_collaborator_id` (`collaborator_id`),
  KEY `idx_annotation_assignment_collaborator` (`annotation_id`, `collaborator_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='标注样本协作分配';
