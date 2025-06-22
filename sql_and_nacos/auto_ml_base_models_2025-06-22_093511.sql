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
-- Dumping data for table `base_models`
--

/*!40000 ALTER TABLE `base_models` DISABLE KEYS */;
INSERT INTO `base_models` VALUES (1,'2025-05-05 11:33:13','2025-05-05 11:34:25','yolov8n.pt',1,0),(2,'2025-05-05 11:33:21','2025-05-05 11:34:25','yolov8s.pt',1,0),(3,'2025-05-05 11:33:27','2025-05-05 11:34:25','yolov8m.pt',1,0),(4,'2025-05-05 11:33:34','2025-05-05 11:34:25','yolov8l.pt',1,0),(5,'2025-05-05 11:34:06','2025-05-05 11:34:25','yolov8x.pt',1,0),(6,'2025-05-05 11:35:32','2025-05-05 11:35:32','yolo11n.pt',1,0),(7,'2025-05-05 11:35:40','2025-05-05 11:35:40','yolo11s.pt',1,0),(8,'2025-05-05 11:35:48','2025-05-05 11:35:48','yolo11m.pt',1,0),(9,'2025-05-05 11:35:56','2025-05-05 11:35:56','yolo11l.pt',1,0),(10,'2025-05-05 11:36:04','2025-05-05 11:36:04','yolo11x.pt',1,0),(11,'2025-05-17 09:50:06','2025-05-17 09:50:06','yolo11n-cls.pt',0,0),(12,'2025-05-17 09:50:06','2025-05-17 09:50:06','yolo11s-cls.pt',0,0),(13,'2025-05-17 09:50:20','2025-05-17 09:50:20','yolo11m-cls.pt',0,0),(14,'2025-05-17 09:50:33','2025-05-17 09:50:33','yolo11l-cls.pt',0,0),(15,'2025-05-17 09:50:48','2025-05-17 09:50:48','yolo11x-cls.pt',0,0);
/*!40000 ALTER TABLE `base_models` ENABLE KEYS */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-06-22  9:35:14
