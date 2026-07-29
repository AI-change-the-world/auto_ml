-- Keep all executions of one batch annotation setup in a group so incremental
-- runs can exclude samples handled by earlier runs in that same group.

ALTER TABLE `ai_pipeline_batch_run`
  ADD COLUMN `batch_group_id` VARCHAR(64) DEFAULT NULL COMMENT '连续增量批量标注分组ID' AFTER `run_id`,
  ADD KEY `idx_ai_pipeline_batch_run_group` (`batch_group_id`);
