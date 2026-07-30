-- Persist real per-sample execution durations reported by the Sandbox.
-- Apply after 20260728_create_ai_pipeline_batch_annotation.sql.

ALTER TABLE `ai_pipeline_batch_run_item`
  ADD COLUMN `processing_duration_ms` INT DEFAULT NULL COMMENT '样本实际处理耗时（毫秒）' AFTER `finished_at`;
