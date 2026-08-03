-- Optional fixed class names for training code ZIPs. Existing generic packages
-- retain an empty list and continue to receive class names per task request.

SET @training_runtime_code_package_class_names_migration = (
  SELECT IF(
    COUNT(*) = 0,
    'ALTER TABLE `training_runtime_code_package` ADD COLUMN `class_names_json` LONGTEXT NOT NULL DEFAULT (''[]'') COMMENT ''可选固定类别顺序 JSON'' AFTER `input_modes_json`',
    'SELECT 1'
  )
  FROM information_schema.columns
  WHERE table_schema = DATABASE()
    AND table_name = 'training_runtime_code_package'
    AND column_name = 'class_names_json'
);
PREPARE training_runtime_code_package_class_names_statement FROM @training_runtime_code_package_class_names_migration;
EXECUTE training_runtime_code_package_class_names_statement;
DEALLOCATE PREPARE training_runtime_code_package_class_names_statement;
