-- MySQL dump 10.13  Distrib 8.0.19, for macos10.15 (x86_64)
--
-- Host: 127.0.0.1    Database: pychron_support
-- ------------------------------------------------------
-- Server version	8.0.19

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `alembic_version`
--

DROP TABLE IF EXISTS `alembic_version`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `alembic_version` (
  `version_num` varchar(32) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `alembic_version`
--

LOCK TABLES `alembic_version` WRITE;
/*!40000 ALTER TABLE `alembic_version` DISABLE KEYS */;
INSERT INTO `alembic_version` VALUES ('7d8af5fc1ca8');
/*!40000 ALTER TABLE `alembic_version` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `AnalysisChangeTbl`
--

DROP TABLE IF EXISTS `AnalysisChangeTbl`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `AnalysisChangeTbl` (
  `idanalysischangeTbl` int unsigned NOT NULL AUTO_INCREMENT,
  `tag` varchar(40) DEFAULT NULL,
  `timestamp` timestamp NULL DEFAULT NULL,
  `user` varchar(45) DEFAULT NULL,
  `analysisID` int DEFAULT NULL,
  PRIMARY KEY (`idanalysischangeTbl`),
  KEY `analysisID` (`analysisID`),
  KEY `userID` (`user`),
  KEY `tag` (`tag`),
  CONSTRAINT `AnalysisChangeTbl_ibfk_1` FOREIGN KEY (`user`) REFERENCES `UserTbl` (`name`),
  CONSTRAINT `AnalysisChangeTbl_ibfk_2` FOREIGN KEY (`analysisID`) REFERENCES `AnalysisTbl` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `AnalysisChangeTbl`
--

LOCK TABLES `AnalysisChangeTbl` WRITE;
/*!40000 ALTER TABLE `AnalysisChangeTbl` DISABLE KEYS */;
/*!40000 ALTER TABLE `AnalysisChangeTbl` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `AnalysisGroupSetTbl`
--

DROP TABLE IF EXISTS `AnalysisGroupSetTbl`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `AnalysisGroupSetTbl` (
  `id` int NOT NULL AUTO_INCREMENT,
  `analysisID` int DEFAULT NULL,
  `groupID` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `analysisID` (`analysisID`),
  KEY `groupID` (`groupID`),
  CONSTRAINT `AnalysisGroupSetTbl_ibfk_1` FOREIGN KEY (`analysisID`) REFERENCES `AnalysisTbl` (`id`),
  CONSTRAINT `AnalysisGroupSetTbl_ibfk_2` FOREIGN KEY (`groupID`) REFERENCES `AnalysisGroupTbl` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `AnalysisGroupSetTbl`
--

LOCK TABLES `AnalysisGroupSetTbl` WRITE;
/*!40000 ALTER TABLE `AnalysisGroupSetTbl` DISABLE KEYS */;
/*!40000 ALTER TABLE `AnalysisGroupSetTbl` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `AnalysisGroupTbl`
--

DROP TABLE IF EXISTS `AnalysisGroupTbl`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `AnalysisGroupTbl` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(140) DEFAULT NULL,
  `create_date` timestamp NULL DEFAULT NULL,
  `projectID` int DEFAULT NULL,
  `user` varchar(140) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `projectID` (`projectID`),
  KEY `user` (`user`),
  CONSTRAINT `AnalysisGroupTbl_ibfk_1` FOREIGN KEY (`projectID`) REFERENCES `ProjectTbl` (`id`),
  CONSTRAINT `AnalysisGroupTbl_ibfk_2` FOREIGN KEY (`user`) REFERENCES `UserTbl` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `AnalysisGroupTbl`
--

LOCK TABLES `AnalysisGroupTbl` WRITE;
/*!40000 ALTER TABLE `AnalysisGroupTbl` DISABLE KEYS */;
/*!40000 ALTER TABLE `AnalysisGroupTbl` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `AnalysisIntensitiesTbl`
--

DROP TABLE IF EXISTS `AnalysisIntensitiesTbl`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `AnalysisIntensitiesTbl` (
  `id` int NOT NULL AUTO_INCREMENT,
  `analysisID` int DEFAULT NULL,
  `value` float DEFAULT NULL,
  `error` float DEFAULT NULL,
  `n` int DEFAULT NULL,
  `fit` varchar(32) DEFAULT NULL,
  `fit_error_type` varchar(32) DEFAULT NULL,
  `baseline_value` float DEFAULT NULL,
  `baseline_error` float DEFAULT NULL,
  `baseline_n` int DEFAULT NULL,
  `baseline_fit` varchar(32) DEFAULT NULL,
  `baseline_fit_error_type` varchar(32) DEFAULT NULL,
  `blank_value` float DEFAULT NULL,
  `blank_error` float DEFAULT NULL,
  `isotope` varchar(32) DEFAULT NULL,
  `detector` varchar(32) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `analysisID` (`analysisID`),
  CONSTRAINT `AnalysisIntensitiesTbl_ibfk_1` FOREIGN KEY (`analysisID`) REFERENCES `AnalysisTbl` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `AnalysisIntensitiesTbl`
--

LOCK TABLES `AnalysisIntensitiesTbl` WRITE;
/*!40000 ALTER TABLE `AnalysisIntensitiesTbl` DISABLE KEYS */;
/*!40000 ALTER TABLE `AnalysisIntensitiesTbl` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `AnalysisTbl`
--

DROP TABLE IF EXISTS `AnalysisTbl`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `AnalysisTbl` (
  `id` int NOT NULL AUTO_INCREMENT,
  `timestamp` timestamp NULL DEFAULT NULL,
  `uuid` varchar(40) DEFAULT NULL,
  `analysis_type` varchar(45) DEFAULT NULL,
  `aliquot` int DEFAULT NULL,
  `increment` int DEFAULT NULL,
  `irradiation_positionID` int DEFAULT NULL,
  `measurementName` varchar(45) DEFAULT NULL,
  `extractionName` varchar(45) DEFAULT NULL,
  `postEqName` varchar(45) DEFAULT NULL,
  `postMeasName` varchar(45) DEFAULT NULL,
  `mass_spectrometer` varchar(45) DEFAULT NULL,
  `extract_device` varchar(45) DEFAULT NULL,
  `extract_value` float DEFAULT NULL,
  `extract_units` varchar(45) DEFAULT NULL,
  `cleanup` float DEFAULT NULL,
  `duration` float DEFAULT NULL,
  `weight` float DEFAULT NULL,
  `comment` varchar(200) DEFAULT NULL,
  `simple_identifier` int DEFAULT NULL,
  `experiment_type` varchar(32) DEFAULT NULL,
  `pre_cleanup` float DEFAULT NULL,
  `post_cleanup` float DEFAULT NULL,
  `cryo_temperature` float DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `irradiation_positionID` (`irradiation_positionID`),
  KEY `mass_spectrometer` (`mass_spectrometer`),
  KEY `analysistbl_ibfk_3` (`extract_device`),
  KEY `simple_identifier` (`simple_identifier`),
  CONSTRAINT `AnalysisTbl_ibfk_1` FOREIGN KEY (`irradiation_positionID`) REFERENCES `IrradiationPositionTbl` (`id`),
  CONSTRAINT `AnalysisTbl_ibfk_2` FOREIGN KEY (`mass_spectrometer`) REFERENCES `MassSpectrometerTbl` (`name`),
  CONSTRAINT `AnalysisTbl_ibfk_3` FOREIGN KEY (`extract_device`) REFERENCES `ExtractDeviceTbl` (`name`),
  CONSTRAINT `AnalysisTbl_ibfk_4` FOREIGN KEY (`simple_identifier`) REFERENCES `SimpleIdentifierTbl` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `AnalysisTbl`
--

LOCK TABLES `AnalysisTbl` WRITE;
/*!40000 ALTER TABLE `AnalysisTbl` DISABLE KEYS */;
/*!40000 ALTER TABLE `AnalysisTbl` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `CurrentTbl`
--

DROP TABLE IF EXISTS `CurrentTbl`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `CurrentTbl` (
  `id` int NOT NULL AUTO_INCREMENT,
  `timestamp` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `parameterID` int DEFAULT NULL,
  `analysisID` int DEFAULT NULL,
  `unitsID` int DEFAULT NULL,
  `value` double DEFAULT NULL,
  `error` double DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `parameterID` (`parameterID`),
  KEY `analysisID` (`analysisID`),
  KEY `unitsID` (`unitsID`),
  CONSTRAINT `CurrentTbl_ibfk_1` FOREIGN KEY (`parameterID`) REFERENCES `ParameterTbl` (`id`),
  CONSTRAINT `CurrentTbl_ibfk_2` FOREIGN KEY (`analysisID`) REFERENCES `AnalysisTbl` (`id`),
  CONSTRAINT `CurrentTbl_ibfk_3` FOREIGN KEY (`unitsID`) REFERENCES `UnitsTbl` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `CurrentTbl`
--

LOCK TABLES `CurrentTbl` WRITE;
/*!40000 ALTER TABLE `CurrentTbl` DISABLE KEYS */;
/*!40000 ALTER TABLE `CurrentTbl` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ExtractDeviceTbl`
--

DROP TABLE IF EXISTS `ExtractDeviceTbl`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ExtractDeviceTbl` (
  `name` varchar(45) NOT NULL,
  PRIMARY KEY (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ExtractDeviceTbl`
--

LOCK TABLES `ExtractDeviceTbl` WRITE;
/*!40000 ALTER TABLE `ExtractDeviceTbl` DISABLE KEYS */;
INSERT INTO `ExtractDeviceTbl` VALUES ('No Extract Device');
/*!40000 ALTER TABLE `ExtractDeviceTbl` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `InterpretedAgeSetTbl`
--

DROP TABLE IF EXISTS `InterpretedAgeSetTbl`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `InterpretedAgeSetTbl` (
  `idinterpretedagesettbl` int NOT NULL AUTO_INCREMENT,
  `interpreted_ageID` int DEFAULT NULL,
  `analysisID` int DEFAULT NULL,
  `forced_plateau_step` tinyint(1) DEFAULT NULL,
  `plateau_step` tinyint(1) DEFAULT NULL,
  `tag` varchar(80) DEFAULT NULL,
  PRIMARY KEY (`idinterpretedagesettbl`),
  KEY `analysisID` (`analysisID`),
  KEY `interpreted_ageID` (`interpreted_ageID`),
  CONSTRAINT `InterpretedAgeSetTbl_ibfk_1` FOREIGN KEY (`interpreted_ageID`) REFERENCES `InterpretedAgeTbl` (`idinterpretedagetbl`),
  CONSTRAINT `InterpretedAgeSetTbl_ibfk_2` FOREIGN KEY (`analysisID`) REFERENCES `AnalysisTbl` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `InterpretedAgeSetTbl`
--

LOCK TABLES `InterpretedAgeSetTbl` WRITE;
/*!40000 ALTER TABLE `InterpretedAgeSetTbl` DISABLE KEYS */;
/*!40000 ALTER TABLE `InterpretedAgeSetTbl` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `InterpretedAgeTbl`
--

DROP TABLE IF EXISTS `InterpretedAgeTbl`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `InterpretedAgeTbl` (
  `idinterpretedagetbl` int NOT NULL AUTO_INCREMENT,
  `age_kind` varchar(32) DEFAULT NULL,
  `kca_kind` varchar(32) DEFAULT NULL,
  `age` float DEFAULT NULL,
  `age_err` float DEFAULT NULL,
  `display_age_units` varchar(2) DEFAULT NULL,
  `kca` float DEFAULT NULL,
  `kca_err` float DEFAULT NULL,
  `mswd` float DEFAULT NULL,
  `age_error_kind` varchar(80) DEFAULT NULL,
  `include_j_error_in_mean` tinyint(1) DEFAULT NULL,
  `include_j_error_in_plateau` tinyint(1) DEFAULT NULL,
  `include_j_error_in_individual_analyses` tinyint(1) DEFAULT NULL,
  PRIMARY KEY (`idinterpretedagetbl`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `InterpretedAgeTbl`
--

LOCK TABLES `InterpretedAgeTbl` WRITE;
/*!40000 ALTER TABLE `InterpretedAgeTbl` DISABLE KEYS */;
/*!40000 ALTER TABLE `InterpretedAgeTbl` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `IrradiationPositionTbl`
--

DROP TABLE IF EXISTS `IrradiationPositionTbl`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `IrradiationPositionTbl` (
  `id` int NOT NULL AUTO_INCREMENT,
  `identifier` varchar(80) DEFAULT NULL,
  `sampleID` int DEFAULT NULL,
  `levelID` int DEFAULT NULL,
  `position` int DEFAULT NULL,
  `note` blob,
  `weight` float DEFAULT NULL,
  `j` float DEFAULT NULL,
  `j_err` float DEFAULT NULL,
  `packet` varchar(80) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `identifier` (`identifier`),
  KEY `sampleID` (`sampleID`),
  KEY `levelID` (`levelID`),
  CONSTRAINT `IrradiationPositionTbl_ibfk_1` FOREIGN KEY (`sampleID`) REFERENCES `SampleTbl` (`id`),
  CONSTRAINT `IrradiationPositionTbl_ibfk_2` FOREIGN KEY (`levelID`) REFERENCES `LevelTbl` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=5857 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `IrradiationPositionTbl`
--

LOCK TABLES `IrradiationPositionTbl` WRITE;
/*!40000 ALTER TABLE `IrradiationPositionTbl` DISABLE KEYS */;
INSERT INTO `IrradiationPositionTbl` VALUES (73,'a-01-A',1,1,6,'',0,NULL,NULL,NULL),(74,'ba-01-A',2,1,7,'',0,NULL,NULL,NULL),(75,'bc-01-A',4,1,8,'',0,NULL,NULL,NULL),(76,'c-01-A',3,1,9,'',0,NULL,NULL,NULL),(77,'ic-01-A',1,1,10,'',0,NULL,NULL,NULL),(854,'pa',248,NULL,NULL,NULL,NULL,NULL,NULL,NULL),(855,'dg',249,NULL,NULL,NULL,NULL,NULL,NULL,NULL),(5856,'bu-FC-A',5,1,11,'',0,NULL,NULL,NULL);
/*!40000 ALTER TABLE `IrradiationPositionTbl` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `IrradiationTbl`
--

DROP TABLE IF EXISTS `IrradiationTbl`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `IrradiationTbl` (
  `name` varchar(80) DEFAULT NULL,
  `id` int NOT NULL AUTO_INCREMENT,
  `create_date` timestamp NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `IrradiationTbl`
--

LOCK TABLES `IrradiationTbl` WRITE;
/*!40000 ALTER TABLE `IrradiationTbl` DISABLE KEYS */;
INSERT INTO `IrradiationTbl` VALUES ('NoIrradiation',1,'2016-01-01 07:00:00');
/*!40000 ALTER TABLE `IrradiationTbl` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `IRTbl`
--

DROP TABLE IF EXISTS `IRTbl`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `IRTbl` (
  `ir` varchar(32) NOT NULL,
  `principal_investigatorID` int unsigned DEFAULT NULL,
  `institution` varchar(140) DEFAULT NULL,
  `checkin_date` date DEFAULT NULL,
  `lab_contact` varchar(140) DEFAULT NULL,
  `comment` blob,
  PRIMARY KEY (`ir`),
  KEY `principal_investigator_id` (`principal_investigatorID`),
  KEY `lab_contact` (`lab_contact`),
  CONSTRAINT `IRTbl_ibfk_1` FOREIGN KEY (`lab_contact`) REFERENCES `UserTbl` (`name`),
  CONSTRAINT `IRTbl_ibfk_2` FOREIGN KEY (`principal_investigatorID`) REFERENCES `PrincipalInvestigatorTbl` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `IRTbl`
--

LOCK TABLES `IRTbl` WRITE;
/*!40000 ALTER TABLE `IRTbl` DISABLE KEYS */;
/*!40000 ALTER TABLE `IRTbl` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `LevelTbl`
--

DROP TABLE IF EXISTS `LevelTbl`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `LevelTbl` (
  `name` varchar(80) DEFAULT NULL,
  `id` int NOT NULL AUTO_INCREMENT,
  `irradiationID` int DEFAULT NULL,
  `productionID` int DEFAULT NULL,
  `holder` varchar(45) DEFAULT NULL,
  `z` float DEFAULT NULL,
  `note` blob,
  PRIMARY KEY (`id`),
  KEY `irradiationID` (`irradiationID`),
  KEY `productionID` (`productionID`),
  CONSTRAINT `LevelTbl_ibfk_1` FOREIGN KEY (`irradiationID`) REFERENCES `IrradiationTbl` (`id`),
  CONSTRAINT `LevelTbl_ibfk_2` FOREIGN KEY (`productionID`) REFERENCES `ProductionTbl` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `LevelTbl`
--

LOCK TABLES `LevelTbl` WRITE;
/*!40000 ALTER TABLE `LevelTbl` DISABLE KEYS */;
INSERT INTO `LevelTbl` VALUES ('A',1,1,1,'Grid',NULL,NULL);
/*!40000 ALTER TABLE `LevelTbl` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `LoadHolderTbl`
--

DROP TABLE IF EXISTS `LoadHolderTbl`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `LoadHolderTbl` (
  `name` varchar(45) NOT NULL,
  PRIMARY KEY (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `LoadHolderTbl`
--

LOCK TABLES `LoadHolderTbl` WRITE;
/*!40000 ALTER TABLE `LoadHolderTbl` DISABLE KEYS */;
/*!40000 ALTER TABLE `LoadHolderTbl` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `LoadPositionTbl`
--

DROP TABLE IF EXISTS `LoadPositionTbl`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `LoadPositionTbl` (
  `id` int NOT NULL AUTO_INCREMENT,
  `identifier` varchar(80) DEFAULT NULL,
  `position` int DEFAULT NULL,
  `loadName` varchar(45) DEFAULT NULL,
  `weight` float DEFAULT NULL,
  `note` blob,
  `nxtals` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `identifier` (`identifier`),
  KEY `loadName` (`loadName`),
  CONSTRAINT `LoadPositionTbl_ibfk_1` FOREIGN KEY (`identifier`) REFERENCES `IrradiationPositionTbl` (`identifier`),
  CONSTRAINT `LoadPositionTbl_ibfk_2` FOREIGN KEY (`loadName`) REFERENCES `LoadTbl` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `LoadPositionTbl`
--

LOCK TABLES `LoadPositionTbl` WRITE;
/*!40000 ALTER TABLE `LoadPositionTbl` DISABLE KEYS */;
/*!40000 ALTER TABLE `LoadPositionTbl` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `LoadTbl`
--

DROP TABLE IF EXISTS `LoadTbl`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `LoadTbl` (
  `name` varchar(45) NOT NULL,
  `create_date` timestamp NULL DEFAULT NULL,
  `holderName` varchar(45) DEFAULT NULL,
  `archived` tinyint(1) DEFAULT NULL,
  `username` varchar(45) DEFAULT NULL,
  PRIMARY KEY (`name`),
  KEY `LoadTbl_ibfk_2` (`username`),
  CONSTRAINT `LoadTbl_ibfk_2` FOREIGN KEY (`username`) REFERENCES `UserTbl` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `LoadTbl`
--

LOCK TABLES `LoadTbl` WRITE;
/*!40000 ALTER TABLE `LoadTbl` DISABLE KEYS */;
/*!40000 ALTER TABLE `LoadTbl` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `MassSpectrometerTbl`
--

DROP TABLE IF EXISTS `MassSpectrometerTbl`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `MassSpectrometerTbl` (
  `name` varchar(45) NOT NULL,
  `kind` varchar(45) DEFAULT NULL,
  PRIMARY KEY (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `MassSpectrometerTbl`
--

LOCK TABLES `MassSpectrometerTbl` WRITE;
/*!40000 ALTER TABLE `MassSpectrometerTbl` DISABLE KEYS */;
/*!40000 ALTER TABLE `MassSpectrometerTbl` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `MaterialTbl`
--

DROP TABLE IF EXISTS `MaterialTbl`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `MaterialTbl` (
  `name` varchar(80) DEFAULT NULL,
  `id` int NOT NULL AUTO_INCREMENT,
  `grainsize` varchar(80) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=228 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `MaterialTbl`
--

LOCK TABLES `MaterialTbl` WRITE;
/*!40000 ALTER TABLE `MaterialTbl` DISABLE KEYS */;
INSERT INTO `MaterialTbl` VALUES ('Gas',1,NULL),('Blank',2,NULL),('Sanidine',19,NULL),('Feldspar',20,NULL),('Biotite',21,NULL),('Plagioclase',23,NULL),('Groundmass',25,NULL),('Hornblende',33,NULL),('WholeRock',39,NULL),('Background',40,NULL),('Degas',41,NULL),('Pause',42,NULL),('Anorthoclase',91,NULL),('K-Feldspar',92,NULL),('Phlogopite',96,NULL),('Barite',97,NULL),('Muscovite',98,NULL),('K-glass',99,NULL),('CaF2',100,NULL),('Adularia',101,NULL),('Alunite',108,NULL),('ImpactSpherules',115,NULL),('Sericite',116,NULL),('Albite',117,NULL),('NaCl',118,NULL),('Jarosite',129,NULL),('Obsidian',134,NULL),('Trachyandesite',135,NULL),('AndesiticBasalt',136,NULL),('Tuff',137,NULL),('Hawaiite',138,NULL),('BasaltClast',139,NULL),('SandforDetrital',140,NULL),('BasaltFlow',141,NULL),('Leucite',143,NULL),('NotListed',145,NULL),('TraceSanidine',146,NULL),('UncommonSan',147,NULL),('VeryRareSan',148,NULL),('UncommonPlagioclase',149,NULL),('DetritalSanidine',161,NULL),('Nepheline',163,NULL),('DaciteLava',169,NULL),('DaciteDike',170,NULL),('BasaltLava',171,NULL),('Rhyolite',172,NULL),('PorphryriticDike',173,NULL),('Illite',178,NULL),('Maskelynite',179,NULL),('NotKnown',180,NULL),('Orthoclase',181,NULL),('Quartz_w_MI',187,NULL),('Orthoclase/Adularia',189,NULL),('Mica',191,NULL),('Amphibole',192,NULL),('Glass',205,NULL),('Tektite',219,NULL),('KCl',227,NULL);
/*!40000 ALTER TABLE `MaterialTbl` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `MeasuredPositionTbl`
--

DROP TABLE IF EXISTS `MeasuredPositionTbl`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `MeasuredPositionTbl` (
  `id` int NOT NULL AUTO_INCREMENT,
  `position` int DEFAULT NULL,
  `x` float DEFAULT NULL,
  `y` float DEFAULT NULL,
  `z` float DEFAULT NULL,
  `is_degas` tinyint(1) DEFAULT NULL,
  `analysisID` int DEFAULT NULL,
  `loadName` varchar(45) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `analysisID` (`analysisID`),
  KEY `loadName` (`loadName`),
  CONSTRAINT `MeasuredPositionTbl_ibfk_1` FOREIGN KEY (`loadName`) REFERENCES `LoadTbl` (`name`),
  CONSTRAINT `MeasuredPositionTbl_ibfk_2` FOREIGN KEY (`analysisID`) REFERENCES `AnalysisTbl` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `MeasuredPositionTbl`
--

LOCK TABLES `MeasuredPositionTbl` WRITE;
/*!40000 ALTER TABLE `MeasuredPositionTbl` DISABLE KEYS */;
/*!40000 ALTER TABLE `MeasuredPositionTbl` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `MediaTbl`
--

DROP TABLE IF EXISTS `MediaTbl`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `MediaTbl` (
  `id` int NOT NULL AUTO_INCREMENT,
  `analysisID` int DEFAULT NULL,
  `username` varchar(140) DEFAULT NULL,
  `url` text,
  `create_date` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `analysisID` (`analysisID`),
  KEY `username` (`username`),
  CONSTRAINT `MediaTbl_ibfk_1` FOREIGN KEY (`analysisID`) REFERENCES `AnalysisTbl` (`id`),
  CONSTRAINT `MediaTbl_ibfk_2` FOREIGN KEY (`username`) REFERENCES `UserTbl` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `MediaTbl`
--

LOCK TABLES `MediaTbl` WRITE;
/*!40000 ALTER TABLE `MediaTbl` DISABLE KEYS */;
/*!40000 ALTER TABLE `MediaTbl` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ParameterTbl`
--

DROP TABLE IF EXISTS `ParameterTbl`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ParameterTbl` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(40) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ParameterTbl`
--

LOCK TABLES `ParameterTbl` WRITE;
/*!40000 ALTER TABLE `ParameterTbl` DISABLE KEYS */;
/*!40000 ALTER TABLE `ParameterTbl` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `PrincipalInvestigatorTbl`
--

DROP TABLE IF EXISTS `PrincipalInvestigatorTbl`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `PrincipalInvestigatorTbl` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(140) DEFAULT NULL,
  `email` varchar(140) DEFAULT NULL,
  `affiliation` varchar(140) DEFAULT NULL,
  `oid` int DEFAULT NULL,
  `last_name` varchar(140) DEFAULT NULL,
  `first_initial` varchar(10) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=28 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `PrincipalInvestigatorTbl`
--

LOCK TABLES `PrincipalInvestigatorTbl` WRITE;
/*!40000 ALTER TABLE `PrincipalInvestigatorTbl` DISABLE KEYS */;
INSERT INTO `PrincipalInvestigatorTbl` VALUES (27,'ANGL',NULL,'ANGL',27,'ANGL','');
/*!40000 ALTER TABLE `PrincipalInvestigatorTbl` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ProductionTbl`
--

DROP TABLE IF EXISTS `ProductionTbl`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ProductionTbl` (
  `name` varchar(80) DEFAULT NULL,
  `id` int NOT NULL AUTO_INCREMENT,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ProductionTbl`
--

LOCK TABLES `ProductionTbl` WRITE;
/*!40000 ALTER TABLE `ProductionTbl` DISABLE KEYS */;
/*!40000 ALTER TABLE `ProductionTbl` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ProjectTbl`
--

DROP TABLE IF EXISTS `ProjectTbl`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ProjectTbl` (
  `name` varchar(80) DEFAULT NULL,
  `id` int NOT NULL AUTO_INCREMENT,
  `principal_investigatorID` int unsigned NOT NULL,
  `checkin_date` date DEFAULT NULL,
  `lab_contact` varchar(80) DEFAULT NULL,
  `institution` varchar(80) DEFAULT NULL,
  `comment` blob,
  PRIMARY KEY (`id`),
  KEY `principal_investigatorID` (`principal_investigatorID`),
  CONSTRAINT `ProjectTbl_ibfk_1` FOREIGN KEY (`principal_investigatorID`) REFERENCES `PrincipalInvestigatorTbl` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ProjectTbl`
--

LOCK TABLES `ProjectTbl` WRITE;
/*!40000 ALTER TABLE `ProjectTbl` DISABLE KEYS */;
INSERT INTO `ProjectTbl` VALUES ('REFERENCES',1,27,NULL,NULL,NULL,NULL);
/*!40000 ALTER TABLE `ProjectTbl` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `RepositoryAssociationTbl`
--

DROP TABLE IF EXISTS `RepositoryAssociationTbl`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `RepositoryAssociationTbl` (
  `idrepositoryassociationTbl` int NOT NULL AUTO_INCREMENT,
  `repository` varchar(80) DEFAULT NULL,
  `analysisID` int DEFAULT NULL,
  PRIMARY KEY (`idrepositoryassociationTbl`),
  KEY `repository` (`repository`),
  KEY `analysisID` (`analysisID`),
  CONSTRAINT `RepositoryAssociationTbl_ibfk_1` FOREIGN KEY (`repository`) REFERENCES `RepositoryTbl` (`name`),
  CONSTRAINT `RepositoryAssociationTbl_ibfk_2` FOREIGN KEY (`analysisID`) REFERENCES `AnalysisTbl` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `RepositoryAssociationTbl`
--

LOCK TABLES `RepositoryAssociationTbl` WRITE;
/*!40000 ALTER TABLE `RepositoryAssociationTbl` DISABLE KEYS */;
/*!40000 ALTER TABLE `RepositoryAssociationTbl` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `RepositoryTbl`
--

DROP TABLE IF EXISTS `RepositoryTbl`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `RepositoryTbl` (
  `name` varchar(80) NOT NULL,
  `principal_investigatorID` int unsigned DEFAULT NULL,
  PRIMARY KEY (`name`),
  KEY `principal_investigatorID` (`principal_investigatorID`),
  CONSTRAINT `RepositoryTbl_ibfk_1` FOREIGN KEY (`principal_investigatorID`) REFERENCES `PrincipalInvestigatorTbl` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `RepositoryTbl`
--

LOCK TABLES `RepositoryTbl` WRITE;
/*!40000 ALTER TABLE `RepositoryTbl` DISABLE KEYS */;
/*!40000 ALTER TABLE `RepositoryTbl` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `RestrictedNameTbl`
--

DROP TABLE IF EXISTS `RestrictedNameTbl`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `RestrictedNameTbl` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(40) DEFAULT NULL,
  `category` varchar(40) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `RestrictedNameTbl`
--

LOCK TABLES `RestrictedNameTbl` WRITE;
/*!40000 ALTER TABLE `RestrictedNameTbl` DISABLE KEYS */;
/*!40000 ALTER TABLE `RestrictedNameTbl` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `SamplePrepChoicesTbl`
--

DROP TABLE IF EXISTS `SamplePrepChoicesTbl`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `SamplePrepChoicesTbl` (
  `id` int NOT NULL AUTO_INCREMENT,
  `tag` varchar(140) DEFAULT NULL,
  `value` varchar(140) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `SamplePrepChoicesTbl`
--

LOCK TABLES `SamplePrepChoicesTbl` WRITE;
/*!40000 ALTER TABLE `SamplePrepChoicesTbl` DISABLE KEYS */;
/*!40000 ALTER TABLE `SamplePrepChoicesTbl` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `SamplePrepImageTbl`
--

DROP TABLE IF EXISTS `SamplePrepImageTbl`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `SamplePrepImageTbl` (
  `id` int NOT NULL AUTO_INCREMENT,
  `stepID` int DEFAULT NULL,
  `host` varchar(45) DEFAULT NULL,
  `path` varchar(200) DEFAULT NULL,
  `timestamp` datetime DEFAULT NULL,
  `note` blob,
  PRIMARY KEY (`id`),
  KEY `stepID` (`stepID`),
  CONSTRAINT `SamplePrepImageTbl_ibfk_1` FOREIGN KEY (`stepID`) REFERENCES `SamplePrepStepTbl` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `SamplePrepImageTbl`
--

LOCK TABLES `SamplePrepImageTbl` WRITE;
/*!40000 ALTER TABLE `SamplePrepImageTbl` DISABLE KEYS */;
/*!40000 ALTER TABLE `SamplePrepImageTbl` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `SamplePrepSessionTbl`
--

DROP TABLE IF EXISTS `SamplePrepSessionTbl`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `SamplePrepSessionTbl` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(32) DEFAULT NULL,
  `comment` varchar(140) DEFAULT NULL,
  `worker_name` varchar(32) DEFAULT NULL,
  `start_date` date DEFAULT NULL,
  `end_date` date DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `worker_name` (`worker_name`),
  CONSTRAINT `SamplePrepSessionTbl_ibfk_1` FOREIGN KEY (`worker_name`) REFERENCES `SamplePrepWorkerTbl` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `SamplePrepSessionTbl`
--

LOCK TABLES `SamplePrepSessionTbl` WRITE;
/*!40000 ALTER TABLE `SamplePrepSessionTbl` DISABLE KEYS */;
/*!40000 ALTER TABLE `SamplePrepSessionTbl` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `SamplePrepStepTbl`
--

DROP TABLE IF EXISTS `SamplePrepStepTbl`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `SamplePrepStepTbl` (
  `id` int NOT NULL AUTO_INCREMENT,
  `sampleID` int DEFAULT NULL,
  `sessionID` int DEFAULT NULL,
  `crush` varchar(140) DEFAULT NULL,
  `wash` varchar(140) DEFAULT NULL,
  `sieve` varchar(140) DEFAULT NULL,
  `frantz` varchar(140) DEFAULT NULL,
  `acid` varchar(140) DEFAULT NULL,
  `heavy_liquid` varchar(140) DEFAULT NULL,
  `pick` varchar(140) DEFAULT NULL,
  `status` varchar(32) DEFAULT NULL,
  `comment` varchar(300) DEFAULT NULL,
  `timestamp` datetime DEFAULT NULL,
  `added` tinyint(1) DEFAULT NULL,
  `mount` varchar(140) DEFAULT NULL,
  `gold_table` varchar(140) DEFAULT NULL,
  `us_wand` varchar(140) DEFAULT NULL,
  `eds` varchar(140) DEFAULT NULL,
  `cl` varchar(140) DEFAULT NULL,
  `bse` varchar(140) DEFAULT NULL,
  `se` varchar(140) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `sampleID` (`sampleID`),
  KEY `sessionID` (`sessionID`),
  CONSTRAINT `SamplePrepStepTbl_ibfk_1` FOREIGN KEY (`sampleID`) REFERENCES `SampleTbl` (`id`),
  CONSTRAINT `SamplePrepStepTbl_ibfk_2` FOREIGN KEY (`sessionID`) REFERENCES `SamplePrepSessionTbl` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `SamplePrepStepTbl`
--

LOCK TABLES `SamplePrepStepTbl` WRITE;
/*!40000 ALTER TABLE `SamplePrepStepTbl` DISABLE KEYS */;
/*!40000 ALTER TABLE `SamplePrepStepTbl` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `SamplePrepWorkerTbl`
--

DROP TABLE IF EXISTS `SamplePrepWorkerTbl`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `SamplePrepWorkerTbl` (
  `name` varchar(32) NOT NULL,
  `fullname` varchar(45) DEFAULT NULL,
  `email` varchar(45) DEFAULT NULL,
  `phone` varchar(45) DEFAULT NULL,
  `comment` varchar(140) DEFAULT NULL,
  PRIMARY KEY (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `SamplePrepWorkerTbl`
--

LOCK TABLES `SamplePrepWorkerTbl` WRITE;
/*!40000 ALTER TABLE `SamplePrepWorkerTbl` DISABLE KEYS */;
/*!40000 ALTER TABLE `SamplePrepWorkerTbl` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `SampleTbl`
--

DROP TABLE IF EXISTS `SampleTbl`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `SampleTbl` (
  `name` varchar(80) DEFAULT NULL,
  `id` int NOT NULL AUTO_INCREMENT,
  `materialID` int DEFAULT NULL,
  `projectID` int DEFAULT NULL,
  `note` varchar(140) DEFAULT NULL,
  `igsn` varchar(140) DEFAULT '',
  `lat` double DEFAULT NULL,
  `lon` double DEFAULT NULL,
  `storage_location` varchar(140) DEFAULT NULL,
  `lithology` varchar(140) DEFAULT NULL,
  `location` varchar(140) DEFAULT NULL,
  `approximate_age` float DEFAULT NULL,
  `elevation` float DEFAULT NULL,
  `create_date` datetime DEFAULT NULL,
  `update_date` datetime DEFAULT NULL,
  `lithology_class` varchar(140) DEFAULT NULL,
  `lithology_group` varchar(140) DEFAULT NULL,
  `lithology_type` varchar(140) DEFAULT NULL,
  `unit` varchar(80) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `materialID` (`materialID`),
  KEY `projectID` (`projectID`),
  CONSTRAINT `SampleTbl_ibfk_1` FOREIGN KEY (`materialID`) REFERENCES `MaterialTbl` (`id`),
  CONSTRAINT `SampleTbl_ibfk_2` FOREIGN KEY (`projectID`) REFERENCES `ProjectTbl` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=250 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `SampleTbl`
--

LOCK TABLES `SampleTbl` WRITE;
/*!40000 ALTER TABLE `SampleTbl` DISABLE KEYS */;
INSERT INTO `SampleTbl` VALUES ('air',1,1,1,NULL,'',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),('blank_air',2,2,1,NULL,'',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),('cocktail',3,1,1,NULL,'',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),('blank_cocktail',4,2,1,NULL,'',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),('blank_unknown',5,2,1,NULL,'',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),('background',247,40,1,NULL,'',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),('pause',248,42,1,NULL,'',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),('degas',249,41,1,NULL,'',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL);
/*!40000 ALTER TABLE `SampleTbl` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `SensitivityTbl`
--

DROP TABLE IF EXISTS `SensitivityTbl`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `SensitivityTbl` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `mass_spectrometer` varchar(45) DEFAULT NULL,
  `value` double DEFAULT '0',
  `timestamp` datetime NOT NULL,
  `note` blob,
  PRIMARY KEY (`id`),
  KEY `mass_spectrometer` (`mass_spectrometer`),
  CONSTRAINT `SensitivityTbl_ibfk_1` FOREIGN KEY (`mass_spectrometer`) REFERENCES `MassSpectrometerTbl` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `SensitivityTbl`
--

LOCK TABLES `SensitivityTbl` WRITE;
/*!40000 ALTER TABLE `SensitivityTbl` DISABLE KEYS */;
/*!40000 ALTER TABLE `SensitivityTbl` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `SimpleIdentifierTbl`
--

DROP TABLE IF EXISTS `SimpleIdentifierTbl`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `SimpleIdentifierTbl` (
  `id` int NOT NULL AUTO_INCREMENT,
  `sampleID` int DEFAULT NULL,
  `identifier` varchar(140) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `SimpleIdentifierTbl_identifier_uindex` (`identifier`),
  KEY `sampleID` (`sampleID`),
  CONSTRAINT `SimpleIdentifierTbl_ibfk_1` FOREIGN KEY (`sampleID`) REFERENCES `SampleTbl` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `SimpleIdentifierTbl`
--

LOCK TABLES `SimpleIdentifierTbl` WRITE;
/*!40000 ALTER TABLE `SimpleIdentifierTbl` DISABLE KEYS */;
/*!40000 ALTER TABLE `SimpleIdentifierTbl` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `TagTbl`
--

DROP TABLE IF EXISTS `TagTbl`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `TagTbl` (
  `name` varchar(40) NOT NULL,
  `omit_ideo` tinyint(1) DEFAULT NULL,
  `omit_spec` tinyint(1) DEFAULT NULL,
  `omit_series` tinyint(1) DEFAULT NULL,
  `omit_iso` tinyint(1) DEFAULT NULL,
  PRIMARY KEY (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `TagTbl`
--

LOCK TABLES `TagTbl` WRITE;
/*!40000 ALTER TABLE `TagTbl` DISABLE KEYS */;
/*!40000 ALTER TABLE `TagTbl` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `UnitsTbl`
--

DROP TABLE IF EXISTS `UnitsTbl`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `UnitsTbl` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(40) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `UnitsTbl`
--

LOCK TABLES `UnitsTbl` WRITE;
/*!40000 ALTER TABLE `UnitsTbl` DISABLE KEYS */;
/*!40000 ALTER TABLE `UnitsTbl` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `UserTbl`
--

DROP TABLE IF EXISTS `UserTbl`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `UserTbl` (
  `name` varchar(45) NOT NULL,
  `affiliation` varchar(80) DEFAULT NULL,
  `category` varchar(80) DEFAULT NULL,
  `email` varchar(80) DEFAULT NULL,
  PRIMARY KEY (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `UserTbl`
--

LOCK TABLES `UserTbl` WRITE;
/*!40000 ALTER TABLE `UserTbl` DISABLE KEYS */;
/*!40000 ALTER TABLE `UserTbl` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `VersionTbl`
--

DROP TABLE IF EXISTS `VersionTbl`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `VersionTbl` (
  `version` varchar(40) NOT NULL,
  PRIMARY KEY (`version`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `VersionTbl`
--

LOCK TABLES `VersionTbl` WRITE;
/*!40000 ALTER TABLE `VersionTbl` DISABLE KEYS */;
INSERT INTO `VersionTbl` VALUES ('7d8af5fc1ca8');
/*!40000 ALTER TABLE `VersionTbl` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2023-01-12  9:16:09
