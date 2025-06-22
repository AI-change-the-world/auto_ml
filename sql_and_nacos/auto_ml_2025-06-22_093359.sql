-- MySQL dump 10.13  Distrib 5.7.24, for osx11.1 (x86_64)
--
-- Host: 127.0.0.1    Database: auto_ml
-- ------------------------------------------------------
-- Server version	9.2.0

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `agent`
--

DROP TABLE IF EXISTS `agent`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `agent` (
  `agent_id` bigint NOT NULL AUTO_INCREMENT,
  `agent_name` varchar(255) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `description` varchar(1024) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `pipeline_file_path` varchar(1024) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `pipeline_content` text COLLATE utf8mb4_general_ci,
  `is_embedded` int DEFAULT '1',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `is_deleted` tinyint(1) DEFAULT '0',
  `is_recommended` tinyint(1) DEFAULT '0',
  `module` varchar(100) COLLATE utf8mb4_general_ci DEFAULT 'annotation',
  PRIMARY KEY (`agent_id`)
) ENGINE=InnoDB AUTO_INCREMENT=10 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `annotation`
--

DROP TABLE IF EXISTS `annotation`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `annotation` (
  `annotation_id` bigint NOT NULL AUTO_INCREMENT,
  `dataset_id` bigint DEFAULT NULL,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `is_deleted` tinyint DEFAULT '0',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `annotation_type` int DEFAULT '1' COMMENT '类型 0分类 1 检测 2 分割 3 其它',
  `class_items` text COLLATE utf8mb4_general_ci COMMENT 'classes, like person,bike..., seperated by ;',
  `annotation_path` varchar(255) COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT 'annotations saved path, if null, annotations will be saved with dataset',
  `storage_type` int DEFAULT '0',
  `annotation_save_path` varchar(1024) COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '标注存储路径',
  `prompt` varchar(2048) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `details` text COLLATE utf8mb4_general_ci,
  PRIMARY KEY (`annotation_id`)
) ENGINE=InnoDB AUTO_INCREMENT=15 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `annotation_file`
--

DROP TABLE IF EXISTS `annotation_file`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `annotation_file` (
  `file_id` bigint NOT NULL AUTO_INCREMENT,
  `annotation_id` bigint DEFAULT NULL,
  `file_path` varchar(255) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `is_deleted` tinyint DEFAULT '0',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `storage_type` int DEFAULT '0',
  PRIMARY KEY (`file_id`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `available_models`
--

DROP TABLE IF EXISTS `available_models`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `available_models` (
  `available_model_id` bigint NOT NULL AUTO_INCREMENT,
  `save_path` varchar(255) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `base_model_name` varchar(255) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `loss` double DEFAULT NULL,
  `epoch` int DEFAULT NULL,
  `dataset_id` bigint DEFAULT NULL,
  `annotation_id` bigint DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `is_deleted` tinyint(1) DEFAULT '0',
  `model_type` varchar(40) COLLATE utf8mb4_general_ci DEFAULT 'detection',
  PRIMARY KEY (`available_model_id`)
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `base_models`
--

DROP TABLE IF EXISTS `base_models`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `base_models` (
  `base_model_id` int NOT NULL AUTO_INCREMENT COMMENT 'Primary Key',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'Create Time',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Update Time',
  `base_model_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `base_model_type` tinyint DEFAULT NULL COMMENT 'base model type, 0 classification, 1 detection, 2 segmentation, 3 other',
  `is_deleted` tinyint DEFAULT '0',
  PRIMARY KEY (`base_model_id`)
) ENGINE=InnoDB AUTO_INCREMENT=16 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='base models';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `dataset`
--

DROP TABLE IF EXISTS `dataset`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `dataset` (
  `dataset_id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键',
  `dataset_name` varchar(255) NOT NULL COMMENT '数据集名称',
  `description` varchar(1024) DEFAULT NULL COMMENT '数据集描述',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `is_deleted` tinyint(1) NOT NULL DEFAULT '0' COMMENT '逻辑删除标志',
  `dataset_type` int NOT NULL DEFAULT '0' COMMENT '数据集类型：0-image，1-text，2-video，3-audio，4-other',
  `ranking` double DEFAULT '0' COMMENT '排序/评分',
  `storage_type` int DEFAULT NULL COMMENT '存储类型',
  `url` varchar(1024) DEFAULT NULL COMMENT '数据源URL',
  `username` varchar(255) DEFAULT NULL COMMENT '存储访问用户名',
  `password` varchar(255) DEFAULT NULL COMMENT '存储访问密码',
  `scan_status` int DEFAULT '0' COMMENT '扫描状态：0-scanning，1-success，2-failed',
  `file_count` int DEFAULT '0',
  `sample_file_path` varchar(255) DEFAULT NULL,
  `local_s3_storage_path` varchar(1024) DEFAULT NULL COMMENT '2025-05-03,本地对象存储路径',
  PRIMARY KEY (`dataset_id`)
) ENGINE=InnoDB AUTO_INCREMENT=13 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='数据集（含存储信息）表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `dataset_file`
--

DROP TABLE IF EXISTS `dataset_file`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `dataset_file` (
  `file_id` bigint NOT NULL AUTO_INCREMENT,
  `dataset_id` bigint DEFAULT NULL,
  `file_path` varchar(255) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `is_deleted` tinyint DEFAULT '0',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`file_id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `predict_data`
--

DROP TABLE IF EXISTS `predict_data`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `predict_data` (
  `predict_data_id` bigint NOT NULL AUTO_INCREMENT COMMENT '预测数据ID',
  `storage_type` int NOT NULL COMMENT '存储类型 (0: 本地文件, 1: S3, 2: WebDAV)',
  `data_type` int NOT NULL COMMENT '数据类型 (0: 图片, 1: 文本, 2: 视频, 3: 音频, 4: 其他)',
  `url` varchar(1024) NOT NULL COMMENT '数据的URL地址',
  `file_name` varchar(255) NOT NULL COMMENT '文件名',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `is_deleted` int NOT NULL DEFAULT '0' COMMENT '是否已删除（逻辑删除）',
  PRIMARY KEY (`predict_data_id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='预测数据表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `predict_task`
--

DROP TABLE IF EXISTS `predict_task`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `predict_task` (
  `task_id` bigint NOT NULL AUTO_INCREMENT COMMENT '任务ID',
  `session_id` varchar(255) NOT NULL COMMENT '会话ID',
  `task_data_id` bigint NOT NULL COMMENT '任务数据ID',
  `task_result` varchar(255) NOT NULL COMMENT '任务结果',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `is_deleted` int NOT NULL DEFAULT '0' COMMENT '是否已删除（逻辑删除）',
  PRIMARY KEY (`task_id`)
) ENGINE=InnoDB AUTO_INCREMENT=171 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='预测任务表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `task`
--

DROP TABLE IF EXISTS `task`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `task` (
  `task_id` int NOT NULL AUTO_INCREMENT COMMENT 'task id',
  `task_type` varchar(30) COLLATE utf8mb4_general_ci DEFAULT 'train' COMMENT 'train,test,annotataion...',
  `dataset_id` int DEFAULT NULL COMMENT 'dataset id',
  `annotation_id` int DEFAULT NULL COMMENT 'annotation id',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `is_deleted` tinyint(1) DEFAULT '0',
  `status` int DEFAULT '0' COMMENT '0 pre task, 1 on task,2 post task,3 done, 4 other，5 error',
  `task_config` varchar(1024) COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT 'task config',
  PRIMARY KEY (`task_id`)
) ENGINE=InnoDB AUTO_INCREMENT=88 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='task table';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `task_log`
--

DROP TABLE IF EXISTS `task_log`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `task_log` (
  `task_id` int NOT NULL COMMENT 'task id',
  `log_content` varchar(1024) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='log of tasks';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tool_model`
--

DROP TABLE IF EXISTS `tool_model`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tool_model` (
  `tool_model_id` bigint NOT NULL AUTO_INCREMENT COMMENT 'Primary key ID',
  `tool_model_name` varchar(255) COLLATE utf8mb4_general_ci NOT NULL COMMENT 'Tool model name',
  `tool_model_description` text COLLATE utf8mb4_general_ci COMMENT 'Description of the tool model',
  `tool_model_type` varchar(40) COLLATE utf8mb4_general_ci DEFAULT 'mllm' COMMENT 'yolo, llm, mllm, gd',
  `is_embedded` tinyint(1) DEFAULT '0' COMMENT '0: embedded; 1: remote',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT 'Creation time',
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Update time',
  `is_deleted` tinyint(1) DEFAULT '0' COMMENT 'Logical deletion flag',
  `base_url` varchar(512) COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT 'Base URL for remote models',
  `api_key` varchar(512) COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT 'API Key for accessing the model',
  `model_name` varchar(255) COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT 'Underlying model name',
  `model_save_path` varchar(255) COLLATE utf8mb4_general_ci DEFAULT NULL,
  PRIMARY KEY (`tool_model_id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='Tool model configuration table';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping routines for database 'auto_ml'
--
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-06-22  9:34:01
