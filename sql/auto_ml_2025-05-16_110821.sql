-- MySQL dump 10.13  Distrib 5.7.24, for osx11.1 (x86_64)
--
-- Host: 127.0.0.1    Database: auto_ml
-- ------------------------------------------------------
-- Server version	9.2.0

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */
;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */
;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */
;
/*!40101 SET NAMES utf8 */
;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */
;
/*!40103 SET TIME_ZONE='+00:00' */
;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */
;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */
;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */
;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */
;

--
-- Table structure for table `agent`
--

DROP TABLE IF EXISTS `agent`;
/*!40101 SET @saved_cs_client     = @@character_set_client */
;
/*!40101 SET character_set_client = utf8 */
;
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
) ENGINE = InnoDB AUTO_INCREMENT = 9 DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */
;

--
-- Dumping data for table `agent`
--

/*!40000 ALTER TABLE `agent` DISABLE KEYS */
;
INSERT INTO
    `agent`
VALUES (
        1,
        '自动标注',
        '根据给定的类别，自动标注图形',
        NULL,
        '<?xml version=\"1.0\" encoding=\"UTF-8\"?> <pipeline outputKey=\"1_result\">     <step id=\"1\" name=\"label-image\">         <action class=\"org.xiaoshuyui.automl.module.aether.workflow.action.LabelImageAction\"/>         <aether>             <task>label</task>             <modelId>1</modelId>             <inputType>image</inputType>             <inputKey>imgPath</inputKey>             <extra>                 <entry key=\"annotation_id\" type=\"num\">${annotation_id}</entry>             </extra>         </aether>         <!-- <next>2</next> -->     </step>     <!-- <step id=\"2\" name=\"post-process\">         <action class=\"org.xiaoshuyui.automl.module.aether.workflow.action.PostProcessAction\"/>     </step> --> </pipeline>',
        1,
        '2025-05-10 08:48:03',
        '2025-05-10 10:06:16',
        0,
        0,
        'annotation'
    ),
    (
        2,
        '自动标注（分批次）',
        '根据给定的类别，自动标注图形，效果较好，耗时较长',
        NULL,
        '<?xml version=\"1.0\" encoding=\"UTF-8\"?> <pipeline outputKey=\"1_result\">     <step id=\"1\" name=\"label-image\">         <action class=\"org.xiaoshuyui.automl.module.aether.workflow.action.BatchLabelImageAction\"/>         <aether>             <task>label in batches</task>             <modelId>1</modelId>             <inputType>image</inputType>             <inputKey>imgPath</inputKey>             <extra>                 <entry key=\"annotation_id\" type=\"num\">${annotation_id}</entry>             </extra>         </aether>     </step> </pipeline>',
        1,
        '2025-05-10 08:49:49',
        '2025-05-11 14:00:00',
        0,
        1,
        'annotation'
    ),
    (
        3,
        '自动标注（给定参考）',
        '根据参考进行自动标注',
        NULL,
        '<?xml version=\"1.0\" encoding=\"UTF-8\"?> <pipeline outputKey=\"1_result\">     <step id=\"1\" name=\"label-image\">         <action class=\"org.xiaoshuyui.automl.module.aether.workflow.action.LabelWithRefAction\"/>         <aether>             <task>label with reference</task>             <modelId>1</modelId>             <inputType>image</inputType>             <inputKey>imgPath</inputKey>             <extra>                 <entry key=\"annotation_id\" type=\"num\">${annotation_id}</entry>                 <entry key=\"template_image\" type=\"str\">${template_image}</entry>             </extra>         </aether>     </step> </pipeline>',
        1,
        '2025-05-10 08:50:27',
        '2025-05-10 14:24:21',
        0,
        0,
        'annotation'
    ),
    (
        4,
        '自动标注（根据相似性）',
        '在图中自动标注相似物体，需选中对应类的一个物体',
        NULL,
        '<?xml version=\"1.0\" encoding=\"UTF-8\"?> <pipeline outputKey=\"1_result\">     <step id=\"1\" name=\"label-image\">         <action class=\"org.xiaoshuyui.automl.module.aether.workflow.action.FindSimilarAction\"/>         <aether>             <task>find similar</task>             <modelId>1</modelId>             <inputType>image</inputType>             <inputKey>imgPath</inputKey>             <extra>                 <entry key=\"annotation_id\" type=\"num\">${annotation_id}</entry>                 <entry key=\"left\" type=\"num\">${left}</entry>                 <entry key=\"top\" type=\"num\">${top}</entry>                 <entry key=\"right\" type=\"num\">${right}</entry>                 <entry key=\"bottom\" type=\"num\">${bottom}</entry>                 <entry key=\"label\" type=\"str\">${label}</entry>             </extra>         </aether>     </step> </pipeline>',
        1,
        '2025-05-10 08:51:15',
        '2025-05-10 14:22:45',
        0,
        0,
        'annotation'
    ),
    (
        5,
        '自动标注（GD）',
        '使用Grounding Dino进行自动标注',
        NULL,
        '<?xml version=\"1.0\" encoding=\"UTF-8\"?> <pipeline outputKey=\"1_result\">     <step id=\"1\" name=\"label-image\">         <action class=\"org.xiaoshuyui.automl.module.aether.workflow.action.LabelImageAction\"/>         <aether>             <task>label with gd</task>             <modelId>2</modelId>             <inputType>image</inputType>             <inputKey>imgPath</inputKey>             <extra>                 <entry key=\"annotation_id\" type=\"num\">${annotation_id}</entry>             </extra>         </aether>     </step> </pipeline>',
        1,
        '2025-05-11 13:35:53',
        '2025-05-11 13:38:24',
        0,
        1,
        'annotation'
    ),
    (
        6,
        '对工地进行深度分析',
        '对工地工人工作状况进行深度分析',
        NULL,
        '<?xml version=\"1.0\" encoding=\"UTF-8\"?> <pipeline outputKey=\"2_result\">     <step id=\"1\" name=\"label-image\" outputKey=\"1_result\" outputType=\"org.xiaoshuyui.automl.module.deploy.entity.PredictSingleImageResponse\">         <action class=\"org.xiaoshuyui.automl.module.aether.workflow.action.LabelImageAction\"/>         <aether>             <task>label with gd</task>             <modelId>2</modelId>             <inputType>image</inputType>             <inputKey>imgPath</inputKey>             <extra>                 <entry key=\"annotation_id\" type=\"num\">${annotation_id}</entry>             </extra>         </aether>         <next>2</next>     </step>     <step id=\"2\" name=\"analysis\" outputKey=\"2_result\">         <action class=\"org.xiaoshuyui.automl.module.aether.workflow.action.DeepAnalysisImageAction\"/>         <aether>             <task>deep analysis image</task>             <modelId>1</modelId>             <inputType>image</inputType>             <inputKey>imgPath</inputKey>             <extra>                 <entry key=\"prompt\" type=\"str\">${prompt}</entry>                 <!-- <entry key=\"annotation_id\" type=\"num\">${annotation_id}</entry> -->             </extra>         </aether>     </step> </pipeline>',
        1,
        '2025-05-12 06:29:05',
        '2025-05-12 06:31:12',
        0,
        0,
        'others'
    ),
    (
        7,
        '自动标注数据集',
        '自动对数据集进行标注，是一个异步任务',
        NULL,
        '<?xml version=\"1.0\" encoding=\"UTF-8\"?> <pipeline name=\"label-dataset\" sync=\"false\">     <step id=\"1\" name=\"prepare data\" outputKey=\"1_result\" outputType=\"java.util.List\">         <action class=\"org.xiaoshuyui.automl.module.aether.workflow.action.PrepareDataAction\"/>         <aether>             <task>prepare data</task>             <modelId></modelId>             <inputType>directory</inputType>             <inputKey>imgPath</inputKey>         </aether>         <next>2</next>     </step>     <step id=\"2\" name=\"label image\" loop=\"true\" loopVar=\"item\" inputKey=\"1_result\" inputType=\"java.util.List\" outputKey=\"2_result\" outputType=\"java.util.List\">         <action class=\"org.xiaoshuyui.automl.module.aether.workflow.action.LabelImageAction\"/>         <aether>             <task>label with gd</task>             <modelId>2</modelId>             <inputType>image</inputType>             <inputKey>item</inputKey>             <extra>                 <entry key=\"annotation_id\" type=\"num\">${annotation_id}</entry>             </extra>         </aether>         <next>3</next>     </step>     <step id=\"3\" name=\"check annotation\" loop=\"true\" loopVar=\"item\" inputKey=\"2_result\" inputType=\"java.util.List\" outputKey=\"3_result\" outputType=\"java.util.List\">         <action class=\"org.xiaoshuyui.automl.module.aether.workflow.action.CheckAnnotationAction\"/>         <aether>             <task>check annotation</task>             <modelId>1</modelId>             <inputType>image</inputType>             <inputKey>item</inputKey>             <extra>                 <entry key=\"annotation_id\" type=\"num\">${annotation_id}</entry>                 <entry key=\"annotations\" type=\"str\">${annotation_type}</entry>             </extra>         </aether>         <next>4</next>     </step>     <step id=\"4\" name=\"save annotation\" loop=\"true\" loopVar=\"item\" inputKey=\"3_result\" inputType=\"java.util.List\">         <action class=\"org.xiaoshuyui.automl.module.aether.workflow.action.SaveAnnotationToS3Action\"/>         <aether>             <task>save result</task>             <modelId></modelId>             <inputType>response</inputType>             <inputKey>item</inputKey>             <extra>                 <entry key=\"annotation_id\" type=\"num\">${annotation_id}</entry>             </extra>         </aether>     </step> </pipeline>',
        1,
        '2025-05-13 07:27:44',
        '2025-05-14 06:34:18',
        0,
        1,
        'dataset annotation'
    ),
    (
        8,
        '标注校正',
        '对上一步产生的标注进行修正，避免出现错标的情况',
        NULL,
        NULL,
        1,
        '2025-05-14 00:55:55',
        '2025-05-14 01:00:57',
        1,
        0,
        'others'
    );
/*!40000 ALTER TABLE `agent` ENABLE KEYS */
;

--
-- Table structure for table `annotation`
--

DROP TABLE IF EXISTS `annotation`;
/*!40101 SET @saved_cs_client     = @@character_set_client */
;
/*!40101 SET character_set_client = utf8 */
;
CREATE TABLE `annotation` (
    `annotation_id` bigint NOT NULL AUTO_INCREMENT,
    `dataset_id` bigint DEFAULT NULL,
    `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `is_deleted` tinyint DEFAULT '0',
    `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
    `annotation_type` int DEFAULT '1' COMMENT '类型 0分类 1 检测 2 分割 3 其它',
    `class_items` text COLLATE utf8mb4_general_ci COMMENT 'classes, like person,bike..., seperated by ;',
    `annotation_path` varchar(255) COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT 'annotations saved path, if null, annotations will be saved with dataset',
    `storage_type` int DEFAULT '0',
    `annotation_save_path` varchar(1024) COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '标注存储路径',
    PRIMARY KEY (`annotation_id`)
) ENGINE = InnoDB AUTO_INCREMENT = 11 DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */
;

--
-- Dumping data for table `annotation`
--

/*!40000 ALTER TABLE `annotation` DISABLE KEYS */
;
/*!40000 ALTER TABLE `annotation` ENABLE KEYS */
;

--
-- Table structure for table `annotation_file`
--

DROP TABLE IF EXISTS `annotation_file`;
/*!40101 SET @saved_cs_client     = @@character_set_client */
;
/*!40101 SET character_set_client = utf8 */
;
CREATE TABLE `annotation_file` (
    `file_id` bigint NOT NULL AUTO_INCREMENT,
    `annotation_id` bigint DEFAULT NULL,
    `file_path` varchar(255) COLLATE utf8mb4_general_ci DEFAULT NULL,
    `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `is_deleted` tinyint DEFAULT '0',
    `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
    `storage_type` int DEFAULT '0',
    PRIMARY KEY (`file_id`)
) ENGINE = InnoDB AUTO_INCREMENT = 7 DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */
;

--
-- Dumping data for table `annotation_file`
--

/*!40000 ALTER TABLE `annotation_file` DISABLE KEYS */
;

/*!40000 ALTER TABLE `annotation_file` ENABLE KEYS */
;

--
-- Table structure for table `available_models`
--

DROP TABLE IF EXISTS `available_models`;
/*!40101 SET @saved_cs_client     = @@character_set_client */
;
/*!40101 SET character_set_client = utf8 */
;
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
    PRIMARY KEY (`available_model_id`)
) ENGINE = InnoDB AUTO_INCREMENT = 6 DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */
;

--
-- Dumping data for table `available_models`
--

/*!40000 ALTER TABLE `available_models` DISABLE KEYS */
;

/*!40000 ALTER TABLE `available_models` ENABLE KEYS */
;

--
-- Table structure for table `base_models`
--

DROP TABLE IF EXISTS `base_models`;
/*!40101 SET @saved_cs_client     = @@character_set_client */
;
/*!40101 SET character_set_client = utf8 */
;
CREATE TABLE `base_models` (
    `base_model_id` int NOT NULL AUTO_INCREMENT COMMENT 'Primary Key',
    `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'Create Time',
    `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Update Time',
    `base_model_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
    `base_model_type` tinyint DEFAULT NULL COMMENT 'base model type, 0 classification, 1 detection, 2 segmentation, 3 other',
    `is_deleted` tinyint DEFAULT '0',
    PRIMARY KEY (`base_model_id`)
) ENGINE = InnoDB AUTO_INCREMENT = 11 DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = 'base models';
/*!40101 SET character_set_client = @saved_cs_client */
;

--
-- Dumping data for table `base_models`
--

/*!40000 ALTER TABLE `base_models` DISABLE KEYS */
;
INSERT INTO
    `base_models`
VALUES (
        1,
        '2025-05-05 11:33:13',
        '2025-05-05 11:34:25',
        'yolov8n.pt',
        1,
        0
    ),
    (
        2,
        '2025-05-05 11:33:21',
        '2025-05-05 11:34:25',
        'yolov8s.pt',
        1,
        0
    ),
    (
        3,
        '2025-05-05 11:33:27',
        '2025-05-05 11:34:25',
        'yolov8m.pt',
        1,
        0
    ),
    (
        4,
        '2025-05-05 11:33:34',
        '2025-05-05 11:34:25',
        'yolov8l.pt',
        1,
        0
    ),
    (
        5,
        '2025-05-05 11:34:06',
        '2025-05-05 11:34:25',
        'yolov8x.pt',
        1,
        0
    ),
    (
        6,
        '2025-05-05 11:35:32',
        '2025-05-05 11:35:32',
        'yolo11n.pt',
        1,
        0
    ),
    (
        7,
        '2025-05-05 11:35:40',
        '2025-05-05 11:35:40',
        'yolo11s.pt',
        1,
        0
    ),
    (
        8,
        '2025-05-05 11:35:48',
        '2025-05-05 11:35:48',
        'yolo11m.pt',
        1,
        0
    ),
    (
        9,
        '2025-05-05 11:35:56',
        '2025-05-05 11:35:56',
        'yolo11l.pt',
        1,
        0
    ),
    (
        10,
        '2025-05-05 11:36:04',
        '2025-05-05 11:36:04',
        'yolo11x.pt',
        1,
        0
    );
/*!40000 ALTER TABLE `base_models` ENABLE KEYS */
;

--
-- Table structure for table `dataset`
--

DROP TABLE IF EXISTS `dataset`;
/*!40101 SET @saved_cs_client     = @@character_set_client */
;
/*!40101 SET character_set_client = utf8 */
;
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
) ENGINE = InnoDB AUTO_INCREMENT = 11 DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '数据集（含存储信息）表';
/*!40101 SET character_set_client = @saved_cs_client */
;

--
-- Dumping data for table `dataset`
--

/*!40000 ALTER TABLE `dataset` DISABLE KEYS */
;
/*!40000 ALTER TABLE `dataset` ENABLE KEYS */
;

--
-- Table structure for table `dataset_file`
--

DROP TABLE IF EXISTS `dataset_file`;
/*!40101 SET @saved_cs_client     = @@character_set_client */
;
/*!40101 SET character_set_client = utf8 */
;
CREATE TABLE `dataset_file` (
    `file_id` bigint NOT NULL AUTO_INCREMENT,
    `dataset_id` bigint DEFAULT NULL,
    `file_path` varchar(255) COLLATE utf8mb4_general_ci DEFAULT NULL,
    `is_deleted` tinyint DEFAULT '0',
    `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
    `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`file_id`)
) ENGINE = InnoDB AUTO_INCREMENT = 2 DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */
;

--
-- Dumping data for table `dataset_file`
--

/*!40000 ALTER TABLE `dataset_file` DISABLE KEYS */
;
/*!40000 ALTER TABLE `dataset_file` ENABLE KEYS */
;

--
-- Table structure for table `predict_data`
--

DROP TABLE IF EXISTS `predict_data`;
/*!40101 SET @saved_cs_client     = @@character_set_client */
;
/*!40101 SET character_set_client = utf8 */
;
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
) ENGINE = InnoDB AUTO_INCREMENT = 2 DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '预测数据表';
/*!40101 SET character_set_client = @saved_cs_client */
;

--
-- Dumping data for table `predict_data`
--

/*!40000 ALTER TABLE `predict_data` DISABLE KEYS */
;
/*!40000 ALTER TABLE `predict_data` ENABLE KEYS */
;

--
-- Table structure for table `predict_task`
--

DROP TABLE IF EXISTS `predict_task`;
/*!40101 SET @saved_cs_client     = @@character_set_client */
;
/*!40101 SET character_set_client = utf8 */
;
CREATE TABLE `predict_task` (
    `task_id` bigint NOT NULL AUTO_INCREMENT COMMENT '任务ID',
    `session_id` varchar(255) NOT NULL COMMENT '会话ID',
    `task_data_id` bigint NOT NULL COMMENT '任务数据ID',
    `task_result` varchar(255) NOT NULL COMMENT '任务结果',
    `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    `is_deleted` int NOT NULL DEFAULT '0' COMMENT '是否已删除（逻辑删除）',
    PRIMARY KEY (`task_id`)
) ENGINE = InnoDB AUTO_INCREMENT = 167 DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '预测任务表';
/*!40101 SET character_set_client = @saved_cs_client */
;

--
-- Dumping data for table `predict_task`
--

/*!40000 ALTER TABLE `predict_task` DISABLE KEYS */
;
/*!40000 ALTER TABLE `predict_task` ENABLE KEYS */
;

--
-- Table structure for table `task`
--

DROP TABLE IF EXISTS `task`;
/*!40101 SET @saved_cs_client     = @@character_set_client */
;
/*!40101 SET character_set_client = utf8 */
;
CREATE TABLE `task` (
    `task_id` int NOT NULL AUTO_INCREMENT COMMENT 'task id',
    `task_type` varchar(30) COLLATE utf8mb4_general_ci DEFAULT 'train' COMMENT 'train,test,annotataion...',
    `dataset_id` int DEFAULT NULL COMMENT 'dataset id',
    `annotation_id` int DEFAULT NULL COMMENT 'annotation id',
    `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `is_deleted` tinyint(1) DEFAULT '0',
    `status` int DEFAULT '0' COMMENT '0 pre task, 1 on task,2 post task,3 done, 4 other',
    `task_config` varchar(1024) COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT 'task config',
    PRIMARY KEY (`task_id`)
) ENGINE = InnoDB AUTO_INCREMENT = 39 DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = 'task table';
/*!40101 SET character_set_client = @saved_cs_client */
;

--
-- Dumping data for table `task`
--

/*!40000 ALTER TABLE `task` DISABLE KEYS */
;

/*!40000 ALTER TABLE `task` ENABLE KEYS */
;

--
-- Table structure for table `task_log`
--

DROP TABLE IF EXISTS `task_log`;
/*!40101 SET @saved_cs_client     = @@character_set_client */
;
/*!40101 SET character_set_client = utf8 */
;
CREATE TABLE `task_log` (
    `task_id` int NOT NULL COMMENT 'task id',
    `log_content` varchar(1024) COLLATE utf8mb4_general_ci DEFAULT NULL,
    `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = 'log of tasks';
/*!40101 SET character_set_client = @saved_cs_client */
;

--
-- Dumping data for table `task_log`
--

/*!40000 ALTER TABLE `task_log` DISABLE KEYS */
;
/*!40000 ALTER TABLE `task_log` ENABLE KEYS */
;

--
-- Table structure for table `tool_model`
--

DROP TABLE IF EXISTS `tool_model`;
/*!40101 SET @saved_cs_client     = @@character_set_client */
;
/*!40101 SET character_set_client = utf8 */
;
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
) ENGINE = InnoDB AUTO_INCREMENT = 3 DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = 'Tool model configuration table';
/*!40101 SET character_set_client = @saved_cs_client */
;

--
-- Dumping data for table `tool_model`
--

/*!40000 ALTER TABLE `tool_model` DISABLE KEYS */
;

/*!40000 ALTER TABLE `tool_model` ENABLE KEYS */
;

--
-- Dumping routines for database 'auto_ml'
--
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */
;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */
;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */
;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */
;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */
;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */
;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */
;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */
;

-- Dump completed on 2025-05-16 11:08:53