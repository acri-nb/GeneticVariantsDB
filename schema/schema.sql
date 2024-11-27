-- MySQL dump 10.13  Distrib 5.7.42, for Linux (x86_64)
--
-- Host: localhost    Database: vardb
-- ------------------------------------------------------
-- Server version	5.7.42-0ubuntu0.18.04.1

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
-- Table structure for table `AnnotationVersion`
--

DROP TABLE IF EXISTS `AnnotationVersion`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `AnnotationVersion` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `id` (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `BaseCallVer`
--

DROP TABLE IF EXISTS `BaseCallVer`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `BaseCallVer` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `id` (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `CallData`
--

DROP TABLE IF EXISTS `CallData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `CallData` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `genotype` varchar(50) DEFAULT NULL,
  `geno_qual` varchar(255) DEFAULT NULL,
  `pass_filter` varchar(50) DEFAULT NULL,
  `afreq` varchar(50) DEFAULT NULL,
  `coverage` int(11) DEFAULT NULL,
  `ref_count` varchar(255) DEFAULT NULL,
  `alt_count` varchar(255) DEFAULT NULL,
  `norm_count` float DEFAULT NULL,
  `cn` float DEFAULT NULL,
  `variant` int(11) DEFAULT NULL,
  `sample` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `variant_sample` (`variant`,`sample`),
  KEY `sample` (`sample`),
  CONSTRAINT `CallData_ibfk_1` FOREIGN KEY (`variant`) REFERENCES `VarData` (`id`) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `CallData_ibfk_2` FOREIGN KEY (`sample`) REFERENCES `RunInfo` (`id`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `Chromosomes`
--

DROP TABLE IF EXISTS `Chromosomes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Chromosomes` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `id` (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `DisType`
--

DROP TABLE IF EXISTS `DisType`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `DisType` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `id` (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `Genes`
--

DROP TABLE IF EXISTS `Genes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Genes` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `id` (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `HGVS`
--

DROP TABLE IF EXISTS `HGVS`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `HGVS` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `transcript` int(11) DEFAULT NULL,
  `gene` int(11) DEFAULT NULL,
  `HGVSc` varchar(255) DEFAULT NULL,
  `HGVSp` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `id` (`id`),
  UNIQUE KEY `transcript_HGVSc` (`transcript`,`HGVSc`),
  KEY `gene` (`gene`),
  CONSTRAINT `HGVS_ibfk_1` FOREIGN KEY (`gene`) REFERENCES `Genes` (`id`) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `HGVS_ibfk_2` FOREIGN KEY (`transcript`) REFERENCES `Transcripts` (`id`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `RunInfo`
--

DROP TABLE IF EXISTS `RunInfo`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `RunInfo` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) DEFAULT NULL,
  `sex` varchar(50) DEFAULT NULL,
  `pheno` int(11) DEFAULT NULL,
  `fileformat` varchar(255) DEFAULT NULL,
  `filedate` int(11) DEFAULT NULL,
  `reference` int(11) DEFAULT NULL,
  `OM_anno_version` int(11) DEFAULT NULL,
  `IonWF` int(11) DEFAULT NULL,
  `IonWF_version` int(11) DEFAULT NULL,
  `Cellularity` float DEFAULT NULL,
  `fusionOC` varchar(255) DEFAULT NULL,
  `fusionQC` varchar(255) DEFAULT NULL,
  `fusionReads` int(11) DEFAULT NULL,
  `basecall_ver` int(11) DEFAULT NULL,
  `perc_mapped` float DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `id` (`id`),
  UNIQUE KEY `name` (`name`),
  KEY `fk_reference` (`reference`),
  KEY `fk_annoversion` (`OM_anno_version`),
  KEY `fk_IonWF` (`IonWF`),
  KEY `fk_IonWFversion` (`IonWF_version`),
  KEY `fk_BaseCallVer` (`basecall_ver`),
  KEY `fk_pheno` (`pheno`),
  CONSTRAINT `fk_BaseCallVer` FOREIGN KEY (`basecall_ver`) REFERENCES `BaseCallVer` (`id`) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `fk_IonWF` FOREIGN KEY (`IonWF`) REFERENCES `WorkFlowName` (`id`) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `fk_IonWFversion` FOREIGN KEY (`IonWF_version`) REFERENCES `WorkFlowVer` (`id`) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `fk_annoversion` FOREIGN KEY (`OM_anno_version`) REFERENCES `AnnotationVersion` (`id`) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `fk_pheno` FOREIGN KEY (`pheno`) REFERENCES `DisType` (`id`) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `fk_reference` FOREIGN KEY (`reference`) REFERENCES `ref_genome` (`id`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `Transcripts`
--

DROP TABLE IF EXISTS `Transcripts`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Transcripts` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `id` (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `VarData`
--

DROP TABLE IF EXISTS `VarData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `VarData` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) DEFAULT NULL,
  `chr` int(11) DEFAULT NULL,
  `start` int(11) DEFAULT NULL,
  `len` varchar(50) DEFAULT NULL,
  `ref` varchar(255) DEFAULT NULL,
  `alt` varchar(255) DEFAULT NULL,
  `type` int(11) DEFAULT NULL,
  `annotation` varchar(255) DEFAULT NULL,
  `gene` int(11) DEFAULT NULL,
  `hgvs` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `id` (`id`),
  UNIQUE KEY `name` (`name`),
  KEY `chr` (`chr`),
  KEY `type` (`type`),
  KEY `gene` (`gene`),
  KEY `hgvs` (`hgvs`),
  CONSTRAINT `VarData_ibfk_1` FOREIGN KEY (`chr`) REFERENCES `Chromosomes` (`id`) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `VarData_ibfk_2` FOREIGN KEY (`type`) REFERENCES `VarType` (`id`) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `VarData_ibfk_3` FOREIGN KEY (`gene`) REFERENCES `Genes` (`id`) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `VarData_ibfk_4` FOREIGN KEY (`hgvs`) REFERENCES `HGVS` (`id`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `VarType`
--

DROP TABLE IF EXISTS `VarType`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `VarType` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `id` (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `WorkFlowName`
--

DROP TABLE IF EXISTS `WorkFlowName`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `WorkFlowName` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `id` (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `WorkFlowVer`
--

DROP TABLE IF EXISTS `WorkFlowVer`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `WorkFlowVer` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `id` (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ref_genome`
--

DROP TABLE IF EXISTS `ref_genome`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ref_genome` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `id` (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2024-06-25 13:08:21
