CREATE TABLE IF NOT EXISTS `assistant_config` (
  `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `created_at` DATETIME NULL COMMENT '创建时间',
  `updated_at` DATETIME NULL COMMENT '更新时间',
  `is_deleted` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '逻辑删除标记',
  `config_key` VARCHAR(64) NOT NULL COMMENT '配置稳定标识',
  `enabled` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否启用智能助手',
  `provider_resource_id` BIGINT NULL COMMENT '关联的 Provider 资源ID',
  `system_prompt` TEXT NULL COMMENT '助手系统提示词',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_assistant_config_config_key` (`config_key`),
  KEY `idx_assistant_config_is_deleted` (`is_deleted`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='工作台智能助手配置表';
