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
-- Dumping data for table `agent`
--

/*!40000 ALTER TABLE `agent` DISABLE KEYS */;
INSERT INTO `agent` VALUES (1,'自动标注','根据给定的类别，自动标注图形',NULL,'<?xml version=\"1.0\" encoding=\"UTF-8\"?> <pipeline outputKey=\"1_result\">     <step id=\"1\" name=\"label-image\">         <action class=\"org.xiaoshuyui.automl.module.aether.workflow.action.LabelImageAction\"/>         <aether>             <task>label</task>             <modelId>1</modelId>             <inputType>image</inputType>             <inputKey>imgPath</inputKey>             <extra>                 <entry key=\"annotation_id\" type=\"num\">${annotation_id}</entry>             </extra>         </aether>         <!-- <next>2</next> -->     </step>     <!-- <step id=\"2\" name=\"post-process\">         <action class=\"org.xiaoshuyui.automl.module.aether.workflow.action.PostProcessAction\"/>     </step> --> </pipeline>',1,'2025-05-10 08:48:03','2025-05-10 10:06:16',0,0,'annotation'),(2,'自动标注（分批次）','根据给定的类别，自动标注图形，效果较好，耗时较长',NULL,'<?xml version=\"1.0\" encoding=\"UTF-8\"?> <pipeline outputKey=\"1_result\">     <step id=\"1\" name=\"label-image\">         <action class=\"org.xiaoshuyui.automl.module.aether.workflow.action.BatchLabelImageAction\"/>         <aether>             <task>label in batches</task>             <modelId>1</modelId>             <inputType>image</inputType>             <inputKey>imgPath</inputKey>             <extra>                 <entry key=\"annotation_id\" type=\"num\">${annotation_id}</entry>             </extra>         </aether>     </step> </pipeline>',1,'2025-05-10 08:49:49','2025-05-11 14:00:00',0,1,'annotation'),(3,'自动标注（给定参考）','根据参考进行自动标注',NULL,'<?xml version=\"1.0\" encoding=\"UTF-8\"?> <pipeline outputKey=\"1_result\">     <step id=\"1\" name=\"label-image\">         <action class=\"org.xiaoshuyui.automl.module.aether.workflow.action.LabelWithRefAction\"/>         <aether>             <task>label with reference</task>             <modelId>1</modelId>             <inputType>image</inputType>             <inputKey>imgPath</inputKey>             <extra>                 <entry key=\"annotation_id\" type=\"num\">${annotation_id}</entry>                 <entry key=\"template_image\" type=\"str\">${template_image}</entry>             </extra>         </aether>     </step> </pipeline>',1,'2025-05-10 08:50:27','2025-05-10 14:24:21',0,0,'annotation'),(4,'自动标注（根据相似性）','在图中自动标注相似物体，需选中对应类的一个物体',NULL,'<?xml version=\"1.0\" encoding=\"UTF-8\"?> <pipeline outputKey=\"1_result\">     <step id=\"1\" name=\"label-image\">         <action class=\"org.xiaoshuyui.automl.module.aether.workflow.action.FindSimilarAction\"/>         <aether>             <task>find similar</task>             <modelId>1</modelId>             <inputType>image</inputType>             <inputKey>imgPath</inputKey>             <extra>                 <entry key=\"annotation_id\" type=\"num\">${annotation_id}</entry>                 <entry key=\"left\" type=\"num\">${left}</entry>                 <entry key=\"top\" type=\"num\">${top}</entry>                 <entry key=\"right\" type=\"num\">${right}</entry>                 <entry key=\"bottom\" type=\"num\">${bottom}</entry>                 <entry key=\"label\" type=\"str\">${label}</entry>             </extra>         </aether>     </step> </pipeline>',1,'2025-05-10 08:51:15','2025-05-10 14:22:45',0,0,'annotation'),(5,'自动标注（GD）','使用Grounding Dino进行自动标注',NULL,'<?xml version=\"1.0\" encoding=\"UTF-8\"?> <pipeline outputKey=\"1_result\">     <step id=\"1\" name=\"label-image\">         <action class=\"org.xiaoshuyui.automl.module.aether.workflow.action.LabelImageAction\"/>         <aether>             <task>label with gd</task>             <modelId>2</modelId>             <inputType>image</inputType>             <inputKey>imgPath</inputKey>             <extra>                 <entry key=\"annotation_id\" type=\"num\">${annotation_id}</entry>             </extra>         </aether>     </step> </pipeline>',1,'2025-05-11 13:35:53','2025-05-11 13:38:24',0,1,'annotation'),(6,'对工地进行深度分析','对工地工人工作状况进行深度分析',NULL,'<?xml version=\"1.0\" encoding=\"UTF-8\"?> <pipeline outputKey=\"2_result\">     <step id=\"1\" name=\"label-image\" outputKey=\"1_result\" outputType=\"org.xiaoshuyui.automl.module.deploy.entity.PredictSingleImageResponse\">         <action class=\"org.xiaoshuyui.automl.module.aether.workflow.action.LabelImageAction\"/>         <aether>             <task>label with gd</task>             <modelId>2</modelId>             <inputType>image</inputType>             <inputKey>imgPath</inputKey>             <extra>                 <entry key=\"annotation_id\" type=\"num\">${annotation_id}</entry>             </extra>         </aether>         <next>2</next>     </step>     <step id=\"2\" name=\"analysis\" outputKey=\"2_result\">         <action class=\"org.xiaoshuyui.automl.module.aether.workflow.action.DeepAnalysisImageAction\"/>         <aether>             <task>deep analysis image</task>             <modelId>1</modelId>             <inputType>image</inputType>             <inputKey>imgPath</inputKey>             <extra>                 <entry key=\"prompt\" type=\"str\">${prompt}</entry>                 <!-- <entry key=\"annotation_id\" type=\"num\">${annotation_id}</entry> -->             </extra>         </aether>     </step> </pipeline>',1,'2025-05-12 06:29:05','2025-05-12 06:31:12',0,0,'others'),(7,'自动标注数据集','自动对数据集进行标注，是一个异步任务',NULL,'<?xml version=\"1.0\" encoding=\"UTF-8\"?> <pipeline name=\"label-dataset\" sync=\"false\">     <step id=\"1\" name=\"prepare data\" outputKey=\"1_result\" outputType=\"java.util.List\">         <action class=\"org.xiaoshuyui.automl.module.aether.workflow.action.PrepareDataAction\"/>         <aether>             <task>prepare data</task>             <modelId></modelId>             <inputType>directory</inputType>             <inputKey>imgPath</inputKey>         </aether>         <next>2</next>     </step>     <step id=\"2\" name=\"label image\" loop=\"true\" loopVar=\"item\" inputKey=\"1_result\" inputType=\"java.util.List\" outputKey=\"2_result\" outputType=\"java.util.List\">         <action class=\"org.xiaoshuyui.automl.module.aether.workflow.action.LabelImageAction\"/>         <aether>             <task>label with gd</task>             <modelId>2</modelId>             <inputType>image</inputType>             <inputKey>item</inputKey>             <extra>                 <entry key=\"annotation_id\" type=\"num\">${annotation_id}</entry>             </extra>         </aether>         <next>3</next>     </step>     <step id=\"3\" name=\"check annotation\" loop=\"true\" loopVar=\"item\" inputKey=\"2_result\" inputType=\"java.util.List\" outputKey=\"3_result\" outputType=\"java.util.List\">         <action class=\"org.xiaoshuyui.automl.module.aether.workflow.action.CheckAnnotationAction\"/>         <aether>             <task>check annotation</task>             <modelId>1</modelId>             <inputType>image</inputType>             <inputKey>item</inputKey>             <extra>                 <entry key=\"annotation_id\" type=\"num\">${annotation_id}</entry>                 <entry key=\"annotations\" type=\"str\">${annotation_type}</entry>             </extra>         </aether>         <next>4</next>     </step>     <step id=\"4\" name=\"save annotation\" loop=\"true\" loopVar=\"item\" inputKey=\"3_result\" inputType=\"java.util.List\">         <action class=\"org.xiaoshuyui.automl.module.aether.workflow.action.SaveAnnotationToS3Action\"/>         <aether>             <task>save result</task>             <modelId></modelId>             <inputType>response</inputType>             <inputKey>item</inputKey>             <extra>                 <entry key=\"annotation_id\" type=\"num\">${annotation_id}</entry>             </extra>         </aether>     </step> </pipeline>',1,'2025-05-13 07:27:44','2025-05-14 06:34:18',0,1,'dataset annotation'),(8,'标注校正','对上一步产生的标注进行修正，避免出现错标的情况',NULL,NULL,1,'2025-05-14 00:55:55','2025-05-14 01:00:57',1,0,'others'),(9,'深度描述图像','用大模型对图像进行深度理解，返回图像内容',NULL,'<?xml version=\"1.0\" encoding=\"UTF-8\"?> <pipeline outputKey=\"1_result\" name=\"label-image\" sync=\"true\">     <step id=\"1\" name=\"describe-image\">         <action class=\"org.xiaoshuyui.automl.module.aether.workflow.action.DescribeImageAction\"/>         <aether>             <task>deep describe</task>             <modelId>1</modelId>             <inputType>image</inputType>             <inputKey>imgPath</inputKey>             <extra>                 <entry key=\"annotation_id\" type=\"num\">${annotation_id}</entry>                 <entry key=\"prompt\" type=\"str\">${prompt}</entry>             </extra>         </aether>     </step> </pipeline>',1,'2025-05-17 01:38:58','2025-05-17 01:38:58',0,0,'image describe');
/*!40000 ALTER TABLE `agent` ENABLE KEYS */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-06-22  9:34:47
