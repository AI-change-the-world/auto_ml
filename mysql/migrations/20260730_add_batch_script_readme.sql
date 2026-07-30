-- Persist the optional root README.md from uploaded batch annotation script packages.
-- Apply after 20260728_add_user_batch_scripts.sql.

ALTER TABLE `ai_pipeline_batch_script`
  ADD COLUMN `readme_markdown` LONGTEXT DEFAULT NULL COMMENT 'ZIP 根目录 README.md 内容' AFTER `description`;
