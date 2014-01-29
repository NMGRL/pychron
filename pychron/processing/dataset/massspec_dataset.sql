# ************************************************************
# Sequel Pro SQL dump
# Version 4096
#
# http://www.sequelpro.com/
# http://code.google.com/p/sequel-pro/
#
# Host: 127.0.0.1 (MySQL 5.5.20-log)
# Database: massspec_dataset
# Generation Time: 2014-01-29 04:57:21 +0000
# ************************************************************


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;


# Dump of table AirArgonAnalysisTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `AirArgonAnalysisTable`;

CREATE TABLE `AirArgonAnalysisTable` (
  `AnalysisID` int(8) unsigned NOT NULL DEFAULT '0',
  `LastSaved` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `DataReductionSessionID` mediumint(8) unsigned DEFAULT NULL,
  `Calcd4036Disc` double NOT NULL DEFAULT '0',
  `Calcd4036DiscEr` double NOT NULL DEFAULT '0',
  `Calcd4038Disc` double unsigned NOT NULL DEFAULT '0',
  `Calcd4038DiscEr` double NOT NULL DEFAULT '0',
  `Uncor4036` double NOT NULL DEFAULT '0',
  `Uncor4036Er` double NOT NULL DEFAULT '0',
  `Uncor4038` double NOT NULL DEFAULT '0',
  `Uncor4038Er` double NOT NULL DEFAULT '0',
  `CalcWithRatio` enum('false','true') NOT NULL DEFAULT 'false',
  KEY `AnalysisID` (`AnalysisID`),
  KEY `Calcd4036Disc` (`Calcd4036Disc`),
  KEY `DataReductionSessionID` (`DataReductionSessionID`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;



# Dump of table AirHeliumAnalysisTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `AirHeliumAnalysisTable`;

CREATE TABLE `AirHeliumAnalysisTable` (
  `AnalysisID` int(8) unsigned NOT NULL,
  `LastSaved` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `DataReductionSessionID` mediumint(8) unsigned DEFAULT NULL,
  `Uncor34` double NOT NULL,
  `Uncor34Er` double NOT NULL,
  `Cor34` double NOT NULL,
  `Cor34Er` double NOT NULL,
  `CalcWithRatio` enum('false','true') NOT NULL,
  KEY `AnalysisID` (`AnalysisID`),
  KEY `DataReductionSessionID` (`DataReductionSessionID`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;



# Dump of table AirNeonAnalysisTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `AirNeonAnalysisTable`;

CREATE TABLE `AirNeonAnalysisTable` (
  `AnalysisID` int(8) unsigned NOT NULL,
  `LastSaved` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `DataReductionSessionID` mediumint(8) unsigned DEFAULT NULL,
  `Ne2022Uncor` double NOT NULL,
  `Ne2022UncorEr` double NOT NULL,
  `Ne2022Cor` double NOT NULL,
  `Ne2022CorEr` double NOT NULL,
  `CalcWithRatio` enum('false','true') NOT NULL,
  KEY `AnalysisID` (`AnalysisID`),
  KEY `DataReductionSessionID` (`DataReductionSessionID`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;



# Dump of table AlternateJTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `AlternateJTable`;

CREATE TABLE `AlternateJTable` (
  `IrradPosition` bigint(20) NOT NULL,
  `JSetLabel` char(40) DEFAULT NULL,
  `J` double DEFAULT NULL,
  `JEr` double DEFAULT NULL,
  UNIQUE KEY `UniqueIrradPosSet` (`IrradPosition`,`JSetLabel`),
  KEY `IrradPosition` (`IrradPosition`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;



# Dump of table AnalysesChangeableItemsTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `AnalysesChangeableItemsTable`;

CREATE TABLE `AnalysesChangeableItemsTable` (
  `ChangeableItemsID` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `AnalysisID` int(8) unsigned NOT NULL DEFAULT '0',
  `DataReductionSessionID` mediumint(8) unsigned DEFAULT NULL,
  `LastSaved` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `History` blob NOT NULL,
  `StatusLevel` smallint(6) NOT NULL DEFAULT '0',
  `StatusReason` smallint(6) NOT NULL,
  `MolRefIsot` float DEFAULT NULL,
  `MolRefIsotSpecial` enum('false','true') NOT NULL DEFAULT 'false',
  `Disc` double DEFAULT NULL,
  `DiscEr` double DEFAULT NULL,
  `PreferencesSetID` int(11) NOT NULL DEFAULT '0',
  `Comment` varchar(255) DEFAULT NULL,
  `SignalNormalizationFactor` double NOT NULL,
  `Version` double NOT NULL DEFAULT '0',
  PRIMARY KEY (`ChangeableItemsID`),
  KEY `AnalysisID` (`AnalysisID`),
  KEY `DataReductionSessionID` (`DataReductionSessionID`),
  KEY `DataReductionSessionID_2` (`DataReductionSessionID`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;



# Dump of table AnalysesTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `AnalysesTable`;

CREATE TABLE `AnalysesTable` (
  `AnalysisID` int(8) unsigned NOT NULL AUTO_INCREMENT,
  `RID` varchar(30) NOT NULL DEFAULT '',
  `IrradPosition` bigint(20) NOT NULL,
  `IrradPosSuffix` varchar(20) NOT NULL DEFAULT '',
  `Aliquot` varchar(10) NOT NULL DEFAULT '',
  `Increment` varchar(20) NOT NULL DEFAULT '',
  `IsGp` varchar(15) NOT NULL DEFAULT '',
  `SpecRunType` smallint(5) unsigned NOT NULL DEFAULT '1',
  `SignalRefIsot` char(30) NOT NULL DEFAULT 'Ar40',
  `LastSaved` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `RunDateTime` datetime NOT NULL DEFAULT '0000-00-00 00:00:00',
  `LoginSessionID` mediumint(8) unsigned NOT NULL,
  `DataCollectionSessionID` int(11) NOT NULL DEFAULT '0',
  `SpecSetUpID` int(11) NOT NULL DEFAULT '0',
  `RunScriptID` int(11) NOT NULL DEFAULT '0',
  `SampleLoadingID` smallint(5) unsigned NOT NULL DEFAULT '0',
  `ScanID` int(10) unsigned NOT NULL DEFAULT '0',
  `SpecParametersID` int(8) unsigned NOT NULL,
  `ExtractionLineConfigID` tinyint(3) unsigned NOT NULL DEFAULT '0',
  `FractionDeliveredToMS` float NOT NULL DEFAULT '1',
  `FirstStageDly` mediumint(8) unsigned NOT NULL DEFAULT '0',
  `SecondStageDly` mediumint(8) unsigned NOT NULL DEFAULT '0',
  `HeatingItemName` varchar(25) NOT NULL DEFAULT '',
  `BeamDiam` float NOT NULL DEFAULT '0',
  `FinalSetPwr` float NOT NULL DEFAULT '0',
  `PwrAchieved` float NOT NULL DEFAULT '0',
  `PwrAchievedSD` float NOT NULL,
  `PwrAchieved_Max` float NOT NULL,
  `OPTemp` float NOT NULL DEFAULT '0',
  `TotDurHeating` mediumint(8) unsigned NOT NULL DEFAULT '0',
  `TotDurHeatingAtReqPwr` mediumint(8) unsigned NOT NULL DEFAULT '0',
  `ReferenceDetectorLabel` varchar(35) NOT NULL DEFAULT '',
  `DataCollectionVersion` float NOT NULL DEFAULT '0',
  `Reviewed` enum('false','true') NOT NULL,
  `RefDetID` mediumint(8) unsigned NOT NULL DEFAULT '0',
  `DetInterCalibID` mediumint(8) unsigned NOT NULL,
  `RedundantSampleID` smallint(5) unsigned NOT NULL DEFAULT '0',
  `ChangeableItemsID` int(10) unsigned NOT NULL DEFAULT '0',
  `RedundantUserID` smallint(5) unsigned NOT NULL DEFAULT '0',
  `AssociatedProjectID` mediumint(8) unsigned NOT NULL,
  `TrapCurrent` double NOT NULL,
  `ManifoldOpt` smallint(5) unsigned NOT NULL,
  `PipettedIsotopes` tinyblob,
  `OriginalImportID` char(80) NOT NULL,
  `OriginalImport` blob,
  PRIMARY KEY (`AnalysisID`),
  UNIQUE KEY `RID` (`RID`),
  KEY `IrradPosition` (`IrradPosition`,`IrradPosSuffix`,`Aliquot`,`Increment`),
  KEY `RunDateTime` (`RunDateTime`),
  KEY `LoginSessionID` (`LoginSessionID`),
  KEY `RedundantSampleID` (`RedundantSampleID`),
  KEY `RedundantUserID` (`RedundantUserID`),
  KEY `AssociatedProjectID` (`AssociatedProjectID`),
  KEY `SpecParametersID` (`SpecParametersID`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;



# Dump of table AnalysisIDListTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `AnalysisIDListTable`;

CREATE TABLE `AnalysisIDListTable` (
  `DataReductionRIDSetID` int(11) NOT NULL DEFAULT '0',
  `AnalysisID` int(8) unsigned NOT NULL DEFAULT '0',
  `RunOrder` int(11) DEFAULT NULL,
  KEY `DataReductionRIDSetID` (`DataReductionRIDSetID`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;



# Dump of table AnalysisPositionTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `AnalysisPositionTable`;

CREATE TABLE `AnalysisPositionTable` (
  `PositionID` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `AnalysisID` int(8) unsigned NOT NULL DEFAULT '0',
  `PositionOrder` int(11) NOT NULL DEFAULT '0',
  `Hole` int(11) DEFAULT NULL,
  `X` double DEFAULT NULL,
  `Y` double DEFAULT NULL,
  PRIMARY KEY (`PositionID`),
  KEY `AnalysisID` (`AnalysisID`),
  KEY `Hole` (`Hole`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;



# Dump of table ArArAnalysisTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `ArArAnalysisTable`;

CREATE TABLE `ArArAnalysisTable` (
  `AnalysisID` int(8) unsigned NOT NULL DEFAULT '0',
  `LastSaved` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `DataReductionSessionID` mediumint(8) unsigned DEFAULT NULL,
  `JVal` double DEFAULT NULL,
  `JEr` double DEFAULT NULL,
  `CalcWithRatio` enum('false','true') NOT NULL DEFAULT 'false',
  `Mol39` double NOT NULL DEFAULT '0',
  `Tot40` double NOT NULL DEFAULT '0',
  `Tot40Er` double NOT NULL DEFAULT '0',
  `Tot39` double NOT NULL DEFAULT '0',
  `Tot39Er` double NOT NULL DEFAULT '0',
  `Tot38` double NOT NULL DEFAULT '0',
  `Tot38Er` double NOT NULL DEFAULT '0',
  `Tot37` double NOT NULL DEFAULT '0',
  `Tot37Er` double NOT NULL DEFAULT '0',
  `Tot36` double NOT NULL DEFAULT '0',
  `Tot36Er` double NOT NULL DEFAULT '0',
  `R3639Cor` double NOT NULL DEFAULT '0',
  `ErR3639` double NOT NULL DEFAULT '0',
  `R3739Cor` double NOT NULL DEFAULT '0',
  `ErR3739Cor` double NOT NULL DEFAULT '0',
  `R3839Cor` double NOT NULL DEFAULT '0',
  `ErR3839` double NOT NULL DEFAULT '0',
  `R4039Cor` double NOT NULL DEFAULT '0',
  `ErR4039` double NOT NULL DEFAULT '0',
  `Rad4039` double NOT NULL DEFAULT '0',
  `Rad4039Er` double NOT NULL DEFAULT '0',
  `Cl3839` double NOT NULL DEFAULT '0',
  `PctRad` double NOT NULL DEFAULT '0',
  `PctRadEr` double NOT NULL DEFAULT '0',
  `Pct36Ca` double NOT NULL DEFAULT '0',
  `ClOverK` double NOT NULL DEFAULT '0',
  `ClOverKEr` double NOT NULL DEFAULT '0',
  `CaOverK` double NOT NULL DEFAULT '0',
  `CaOverKEr` double NOT NULL DEFAULT '0',
  `Age` double NOT NULL DEFAULT '0',
  `ErrAgeWOErInJ` double NOT NULL DEFAULT '0',
  `ErrAge` double NOT NULL DEFAULT '0',
  `AgeErMonteCarlo` double NOT NULL DEFAULT '0',
  `ErrAgeWExternal` double NOT NULL DEFAULT '0',
  KEY `AnalysisID` (`AnalysisID`),
  KEY `Age` (`Age`),
  KEY `PctRad` (`PctRad`),
  KEY `DataReductionSessionID` (`DataReductionSessionID`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;



# Dump of table AutocenterTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `AutocenterTable`;

CREATE TABLE `AutocenterTable` (
  `AutocenterID` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `AnalysisID` int(8) NOT NULL DEFAULT '0',
  `IsotopeLabel` varchar(35) NOT NULL DEFAULT '',
  `DetectorLabel` char(35) NOT NULL,
  `ACDateTime` datetime NOT NULL DEFAULT '0000-00-00 00:00:00',
  `PositioningMethod` enum('HV','MF','Mass') NOT NULL,
  `ScanByAV` enum('false','true') NOT NULL DEFAULT 'false',
  `AutocenterBlob` blob,
  `RawIntensityArray` blob,
  `PositionArray` blob,
  `TimeArray` blob,
  `MFCenter` double NOT NULL DEFAULT '0',
  `MFCenterAtNominalHV` double NOT NULL,
  `MassCenter` double NOT NULL DEFAULT '0',
  `HVCenter` double NOT NULL DEFAULT '0',
  `MaxIntensity` double NOT NULL DEFAULT '0',
  `MidSideLow` double NOT NULL DEFAULT '0',
  `MidSideHigh` double NOT NULL DEFAULT '0',
  `Asymmetry` double NOT NULL DEFAULT '0',
  `OnePctLow` double NOT NULL DEFAULT '0',
  `OnePctHigh` double NOT NULL DEFAULT '0',
  `FivePctLow` double NOT NULL DEFAULT '0',
  `FivePctHigh` double NOT NULL DEFAULT '0',
  `SlitWidth` double NOT NULL DEFAULT '0',
  `BeamWidth` double NOT NULL DEFAULT '0',
  `MRP_HighMassSide` double NOT NULL,
  `MRP_LowMassSide` double NOT NULL,
  `CenteringMethod` smallint(5) unsigned NOT NULL DEFAULT '0',
  `Resolution` double NOT NULL DEFAULT '0',
  `DoDriftCorrection` enum('false','true') NOT NULL DEFAULT 'false',
  `InitialHeight` double NOT NULL DEFAULT '0',
  `FinalHeight` double NOT NULL DEFAULT '0',
  `InitialTick` int(10) unsigned NOT NULL DEFAULT '0',
  `FinalTick` int(10) unsigned NOT NULL DEFAULT '0',
  `TimeSeriesNTerms` smallint(5) unsigned NOT NULL DEFAULT '0',
  `Fit` smallint(5) unsigned NOT NULL,
  `PlotRawDataAsCurve` enum('false','true') NOT NULL,
  `LSFParams` blob,
  PRIMARY KEY (`AutocenterID`),
  KEY `AnalysisID` (`AnalysisID`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;



# Dump of table baselineschangeableitemstable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `baselineschangeableitemstable`;

CREATE TABLE `baselineschangeableitemstable` (
  `BslnID` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `LastSaved` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `DataReductionSessionID` mediumint(8) unsigned DEFAULT NULL,
  `Fit` smallint(5) unsigned NOT NULL DEFAULT '0',
  `PDPBlob` blob,
  `InfoBlob` blob,
  KEY `BslnID` (`BslnID`),
  KEY `DataReductionSessionID` (`DataReductionSessionID`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;



# Dump of table baselinestable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `baselinestable`;

CREATE TABLE `baselinestable` (
  `BslnID` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `Label` varchar(35) NOT NULL DEFAULT '',
  `NumCnts` smallint(5) unsigned NOT NULL DEFAULT '0',
  `PeakTimeBlob` blob,
  PRIMARY KEY (`BslnID`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;



# Dump of table Cl35CorrectionTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `Cl35CorrectionTable`;

CREATE TABLE `Cl35CorrectionTable` (
  `RecordID` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `SpecSysN` smallint(6) NOT NULL DEFAULT '0',
  `LastSaved` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `DetectorTypeID` smallint(6) NOT NULL DEFAULT '0',
  `ExtractionLineConfigID` mediumint(8) unsigned DEFAULT NULL,
  `Parameter` double NOT NULL DEFAULT '0',
  `ParameterEr` double DEFAULT NULL,
  `Slope` double DEFAULT NULL,
  `ParameterBlob` blob,
  `StartingDate` datetime NOT NULL DEFAULT '0000-00-00 00:00:00',
  `UserID` smallint(5) unsigned NOT NULL DEFAULT '0',
  PRIMARY KEY (`RecordID`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;



# Dump of table CreateStandardAgeTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `CreateStandardAgeTable`;

CREATE TABLE `CreateStandardAgeTable` (
  `StandardID` smallint(5) unsigned NOT NULL AUTO_INCREMENT,
  `UnitName` char(40) NOT NULL,
  `MaterialID` smallint(5) unsigned NOT NULL,
  `PreparationName` char(40) NOT NULL,
  `Type` tinyint(3) unsigned NOT NULL,
  `Age` double NOT NULL,
  `AgeEr` double NOT NULL,
  PRIMARY KEY (`StandardID`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;



# Dump of table databaseversiontable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `databaseversiontable`;

CREATE TABLE `databaseversiontable` (
  `Version` float NOT NULL DEFAULT '0'
) ENGINE=MyISAM DEFAULT CHARSET=latin1;



# Dump of table DataCollectionSessionTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `DataCollectionSessionTable`;

CREATE TABLE `DataCollectionSessionTable` (
  `DataCollectionSessionID` int(11) NOT NULL DEFAULT '0',
  `Label` varchar(40) NOT NULL DEFAULT '',
  `LastSaved` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `EventDate` timestamp NOT NULL DEFAULT '0000-00-00 00:00:00',
  `Note` text NOT NULL,
  `TheText` text NOT NULL,
  PRIMARY KEY (`DataCollectionSessionID`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;



# Dump of table DataReductionRIDSetTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `DataReductionRIDSetTable`;

CREATE TABLE `DataReductionRIDSetTable` (
  `DataReductionRIDSetID` int(11) NOT NULL DEFAULT '0',
  `LastSaved` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `EventDate` timestamp NOT NULL DEFAULT '0000-00-00 00:00:00',
  `Label` varchar(40) NOT NULL DEFAULT '',
  `Note` text NOT NULL,
  `TheText` blob NOT NULL,
  `ProjectID` mediumint(8) unsigned NOT NULL DEFAULT '0',
  `UserID` smallint(5) unsigned NOT NULL DEFAULT '0',
  `ShowInRunSelection` enum('true','false') NOT NULL DEFAULT 'true',
  PRIMARY KEY (`DataReductionRIDSetID`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;



# Dump of table datareductionsessiontable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `datareductionsessiontable`;

CREATE TABLE `datareductionsessiontable` (
  `DataReductionSessionID` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `DataReductionRIDSetID` int(11) NOT NULL DEFAULT '0',
  `SessionDate` datetime NOT NULL DEFAULT '0000-00-00 00:00:00',
  `UserID` smallint(5) unsigned NOT NULL DEFAULT '0',
  `Description` varchar(40) NOT NULL DEFAULT '',
  PRIMARY KEY (`DataReductionSessionID`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;

LOCK TABLES `datareductionsessiontable` WRITE;
/*!40000 ALTER TABLE `datareductionsessiontable` DISABLE KEYS */;

INSERT INTO `datareductionsessiontable` (`DataReductionSessionID`, `DataReductionRIDSetID`, `SessionDate`, `UserID`, `Description`)
VALUES
	(1,0,'2014-01-28 21:55:18',0,'');

/*!40000 ALTER TABLE `datareductionsessiontable` ENABLE KEYS */;
UNLOCK TABLES;


# Dump of table DetectorICDatedTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `DetectorICDatedTable`;

CREATE TABLE `DetectorICDatedTable` (
  `RecordID` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `SpecSysN` smallint(6) NOT NULL,
  `LastSaved` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `DetectorTypeID` smallint(6) NOT NULL,
  `ExtractionLineConfigID` mediumint(8) unsigned DEFAULT NULL,
  `Parameter` double NOT NULL,
  `ParameterEr` double DEFAULT NULL,
  `Slope` double DEFAULT NULL,
  `ParameterBlob` blob,
  `StartingDate` datetime NOT NULL,
  `UserID` smallint(5) unsigned NOT NULL,
  PRIMARY KEY (`RecordID`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;



# Dump of table DetectorICDetectorTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `DetectorICDetectorTable`;

CREATE TABLE `DetectorICDetectorTable` (
  `Counter` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `LastSaved` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `InterCalibID` mediumint(8) unsigned NOT NULL DEFAULT '0',
  `DetectorTypeID` smallint(6) NOT NULL DEFAULT '0',
  `ICFactor` double NOT NULL DEFAULT '0',
  `ICFactorEr` double NOT NULL DEFAULT '0',
  `RawMeasRatio` double NOT NULL DEFAULT '0',
  `RawMeasRatioEr` double NOT NULL,
  `TrueRatio` double NOT NULL DEFAULT '1',
  `AverageSignal` double NOT NULL,
  `Disc` double NOT NULL DEFAULT '0',
  `DiscEr` double NOT NULL DEFAULT '0',
  `MeasuredIsotope` char(35) NOT NULL DEFAULT '',
  `PeakTimeBlob` blob NOT NULL,
  PRIMARY KEY (`Counter`),
  KEY `InterCalibID` (`InterCalibID`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;



# Dump of table DetectorIntercalibrationTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `DetectorIntercalibrationTable`;

CREATE TABLE `DetectorIntercalibrationTable` (
  `InterCalibID` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `MeasurementDateTime` datetime NOT NULL DEFAULT '0000-00-00 00:00:00',
  `RefDetTypeID` smallint(6) NOT NULL DEFAULT '0',
  `RefIsotope` char(35) NOT NULL DEFAULT '',
  `AverageSignal` double NOT NULL,
  `RefDetDisc` double NOT NULL DEFAULT '0',
  `RefDetDiscEr` double NOT NULL DEFAULT '0',
  `PeakTimeBlob` blob NOT NULL,
  `FitType` smallint(5) unsigned NOT NULL,
  PRIMARY KEY (`InterCalibID`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;



# Dump of table DetectorTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `DetectorTable`;

CREATE TABLE `DetectorTable` (
  `DetectorID` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `LastSaved` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `DetectorTypeID` mediumint(8) unsigned NOT NULL DEFAULT '0',
  `EMV` double NOT NULL DEFAULT '0',
  `Gain` double NOT NULL DEFAULT '0',
  `ICFactor` double NOT NULL DEFAULT '1',
  `Disc` double NOT NULL DEFAULT '1',
  `DiscEr` double NOT NULL DEFAULT '0.00001',
  `DiscSource` tinyint(3) unsigned DEFAULT '2',
  `ScaleFactor` double NOT NULL DEFAULT '0',
  `IonCounterDeadtimeSec` double NOT NULL,
  `Sniff` double NOT NULL,
  `ICFactorEr` double NOT NULL DEFAULT '0',
  `ICFactorSource` tinyint(3) unsigned DEFAULT '5',
  `ConvFactorToRefDetUnits` float NOT NULL DEFAULT '0',
  `Label` char(35) NOT NULL,
  PRIMARY KEY (`DetectorID`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;



# Dump of table DetectorTypeTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `DetectorTypeTable`;

CREATE TABLE `DetectorTypeTable` (
  `DetectorTypeID` smallint(6) NOT NULL,
  `Label` char(35) NOT NULL,
  `ResistorValue` double DEFAULT NULL,
  `ScaleFactor` double DEFAULT NULL,
  PRIMARY KEY (`DetectorTypeID`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;

LOCK TABLES `DetectorTypeTable` WRITE;
/*!40000 ALTER TABLE `DetectorTypeTable` DISABLE KEYS */;

INSERT INTO `DetectorTypeTable` (`DetectorTypeID`, `Label`, `ResistorValue`, `ScaleFactor`)
VALUES
	(1,'Multiplier Analog',1,-1000000000),
	(2,'Multiplier Analog Aux',1,-1000000000),
	(3,'Faraday',100000000000,1),
	(4,'Quadrupole',1,100),
	(5,'Pulse',1,100000),
	(19,'Multiplier Volts',1,1),
	(24,'H2',1000000000000,1),
	(25,'H1',1000000000000,1),
	(26,'AX',1000000000000,1),
	(27,'L1',1000000000000,1),
	(28,'L2',1000000000000,1),
	(29,'CDD',1,1);

/*!40000 ALTER TABLE `DetectorTypeTable` ENABLE KEYS */;
UNLOCK TABLES;


# Dump of table DiscriminationTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `DiscriminationTable`;

CREATE TABLE `DiscriminationTable` (
  `RecordID` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `SpecSysN` smallint(6) NOT NULL DEFAULT '0',
  `LastSaved` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `DetectorTypeID` smallint(6) NOT NULL DEFAULT '0',
  `ExtractionLineConfigID` mediumint(8) unsigned DEFAULT NULL,
  `Parameter` double NOT NULL DEFAULT '0',
  `ParameterEr` double DEFAULT NULL,
  `Slope` double DEFAULT NULL,
  `ParameterBlob` blob,
  `StartingDate` datetime NOT NULL DEFAULT '0000-00-00 00:00:00',
  `UserID` smallint(5) unsigned NOT NULL DEFAULT '0',
  PRIMARY KEY (`RecordID`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;



# Dump of table fittypetable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `fittypetable`;

CREATE TABLE `fittypetable` (
  `Fit` smallint(6) NOT NULL DEFAULT '0',
  `Label` varchar(60) DEFAULT NULL,
  PRIMARY KEY (`Fit`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;



# Dump of table GraphicsProjectAssociationTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `GraphicsProjectAssociationTable`;

CREATE TABLE `GraphicsProjectAssociationTable` (
  `GraphicsID` int(10) unsigned NOT NULL,
  `ID` mediumint(8) unsigned NOT NULL,
  KEY `GraphicsID` (`GraphicsID`),
  KEY `ID` (`ID`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;



# Dump of table GraphicsSampleAssociationTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `GraphicsSampleAssociationTable`;

CREATE TABLE `GraphicsSampleAssociationTable` (
  `GraphicsID` int(10) unsigned NOT NULL,
  `ID` mediumint(8) unsigned NOT NULL,
  KEY `GraphicsID` (`GraphicsID`),
  KEY `ID` (`ID`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;



# Dump of table GraphicsTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `GraphicsTable`;

CREATE TABLE `GraphicsTable` (
  `GraphicsID` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `Label` char(60) NOT NULL,
  `Type` smallint(5) unsigned NOT NULL,
  `LastSaved` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `Preview` blob NOT NULL,
  `JPEG` blob NOT NULL,
  `TheText` blob NOT NULL,
  PRIMARY KEY (`GraphicsID`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;



# Dump of table HeliumAnalysisTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `HeliumAnalysisTable`;

CREATE TABLE `HeliumAnalysisTable` (
  `AnalysisID` int(8) unsigned NOT NULL,
  `LastSaved` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `DataReductionSessionID` mediumint(8) unsigned DEFAULT NULL,
  `He34Uncor` double DEFAULT NULL,
  `He34UncorEr` double DEFAULT NULL,
  `He34Cor` double DEFAULT NULL,
  `He34CorEr` double DEFAULT NULL,
  `He34SensCal` double DEFAULT NULL,
  `He34SensCalEr` double DEFAULT NULL,
  `He34VolCal` double DEFAULT NULL,
  `He34VolCalEr` double DEFAULT NULL,
  KEY `AnalysisID` (`AnalysisID`),
  KEY `DataReductionSessionID` (`DataReductionSessionID`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;



# Dump of table irradiationchronologytable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `irradiationchronologytable`;

CREATE TABLE `irradiationchronologytable` (
  `IrradBaseID` varchar(25) NOT NULL DEFAULT '',
  `LastSaved` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `StartTime` datetime NOT NULL DEFAULT '0000-00-00 00:00:00',
  `EndTime` datetime NOT NULL DEFAULT '0000-00-00 00:00:00'
) ENGINE=MyISAM DEFAULT CHARSET=latin1;



# Dump of table IrradiationLevelTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `IrradiationLevelTable`;

CREATE TABLE `IrradiationLevelTable` (
  `IrradBaseID` varchar(25) NOT NULL DEFAULT '',
  `Level` varchar(25) NOT NULL DEFAULT '',
  `LastSaved` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `ExperimentType` smallint(5) unsigned NOT NULL DEFAULT '1',
  `JSetLabel` char(40) DEFAULT NULL,
  `LegacyJ` double NOT NULL DEFAULT '0',
  `LegacyJEr` double NOT NULL DEFAULT '0',
  `Note` blob NOT NULL,
  `ProductionRatiosID` int(11) NOT NULL DEFAULT '0',
  `SampleHolder` varchar(40) NOT NULL DEFAULT '',
  PRIMARY KEY (`IrradBaseID`,`Level`),
  KEY `IrradBaseID` (`IrradBaseID`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;



# Dump of table IrradiationPositionTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `IrradiationPositionTable`;

CREATE TABLE `IrradiationPositionTable` (
  `IrradPosition` bigint(20) NOT NULL,
  `IrradiationLevel` char(60) NOT NULL,
  `LastSaved` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `HoleNumber` mediumint(8) unsigned NOT NULL DEFAULT '0',
  `Material` varchar(30) NOT NULL DEFAULT '',
  `SampleID` mediumint(8) unsigned NOT NULL DEFAULT '0',
  `Size` varchar(30) NOT NULL DEFAULT '',
  `Weight` double NOT NULL DEFAULT '0',
  `Note` varchar(255) DEFAULT NULL,
  `LabActivation` datetime NOT NULL,
  `J` double DEFAULT NULL,
  `JEr` double DEFAULT NULL,
  `StandardID` smallint(5) unsigned NOT NULL,
  PRIMARY KEY (`IrradPosition`),
  KEY `Material` (`Material`),
  KEY `SampleID` (`SampleID`),
  KEY `IrradiationLevel` (`IrradiationLevel`),
  KEY `IrradiationLevel_2` (`IrradiationLevel`),
  KEY `IrradiationLevel_3` (`IrradiationLevel`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;

LOCK TABLES `IrradiationPositionTable` WRITE;
/*!40000 ALTER TABLE `IrradiationPositionTable` DISABLE KEYS */;

INSERT INTO `IrradiationPositionTable` (`IrradPosition`, `IrradiationLevel`, `LastSaved`, `HoleNumber`, `Material`, `SampleID`, `Size`, `Weight`, `Note`, `LabActivation`, `J`, `JEr`, `StandardID`)
VALUES
	(19211,'NM-205E','2014-01-28 21:55:18',7,'',0,'NULL',0,NULL,'0000-00-00 00:00:00',NULL,NULL,0);

/*!40000 ALTER TABLE `IrradiationPositionTable` ENABLE KEYS */;
UNLOCK TABLES;


# Dump of table IrradiationProductionTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `IrradiationProductionTable`;

CREATE TABLE `IrradiationProductionTable` (
  `ProductionRatiosID` int(11) NOT NULL DEFAULT '0',
  `Counter` smallint(5) unsigned NOT NULL AUTO_INCREMENT,
  `LastSaved` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `Label` char(40) NOT NULL,
  `Ca3637` double NOT NULL DEFAULT '0',
  `Ca3637Er` double NOT NULL DEFAULT '0',
  `Ca3937` double NOT NULL DEFAULT '0',
  `Ca3937Er` double NOT NULL DEFAULT '0',
  `K4039` double NOT NULL DEFAULT '0',
  `K4039Er` double NOT NULL DEFAULT '0',
  `P36Cl38Cl` double NOT NULL DEFAULT '0',
  `P36Cl38ClEr` double NOT NULL DEFAULT '0',
  `Ca3837` double NOT NULL DEFAULT '0',
  `Ca3837Er` double NOT NULL DEFAULT '0',
  `K3839` double NOT NULL DEFAULT '0',
  `K3839Er` double NOT NULL DEFAULT '0',
  `K3739` double NOT NULL,
  `K3739Er` double NOT NULL,
  `ClOverKMultiplier` double NOT NULL DEFAULT '0',
  `ClOverKMultiplierEr` double NOT NULL DEFAULT '0',
  `CaOverKMultiplier` double NOT NULL DEFAULT '0',
  `CaOverKMultiplierEr` double NOT NULL DEFAULT '0',
  `ReactorName` char(40) DEFAULT NULL,
  PRIMARY KEY (`ProductionRatiosID`),
  KEY `Counter` (`Counter`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;



# Dump of table IsotopeResultsTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `IsotopeResultsTable`;

CREATE TABLE `IsotopeResultsTable` (
  `Counter` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `LastSaved` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `IsotopeID` int(10) unsigned NOT NULL DEFAULT '0',
  `DataReductionSessionID` mediumint(8) unsigned NOT NULL DEFAULT '0',
  `InterceptEr` double NOT NULL DEFAULT '0',
  `Intercept` double NOT NULL DEFAULT '0',
  `Iso` double NOT NULL DEFAULT '0',
  `IsoEr` double NOT NULL DEFAULT '0',
  `CalibMolesPerSignalAtUnitGain` double DEFAULT NULL,
  `CalibMolesPerSignalAtUnitGainEr` double DEFAULT NULL,
  `SensCalibMoles` double DEFAULT NULL,
  `SensCalibMolesEr` double DEFAULT NULL,
  `VolumeCalibFactor` double DEFAULT NULL,
  `VolumeCalibFactorEr` double DEFAULT NULL,
  `VolumeCalibratedValue` double DEFAULT NULL,
  `VolumeCalibratedValueEr` double DEFAULT NULL,
  `Bkgd` double DEFAULT NULL,
  `BkgdEr` double DEFAULT NULL,
  `BkgdDetTypeID` tinyint(4) NOT NULL,
  `PkHtChangePct` double DEFAULT NULL,
  `Fit` tinyint(4) DEFAULT NULL,
  `GOF` double DEFAULT NULL,
  `PeakScaleFactor` double DEFAULT NULL,
  PRIMARY KEY (`Counter`),
  KEY `IsotopeID` (`IsotopeID`),
  KEY `DataReductionSessionID` (`DataReductionSessionID`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;



# Dump of table IsotopeTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `IsotopeTable`;

CREATE TABLE `IsotopeTable` (
  `IsotopeID` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `TypeID` tinyint(3) unsigned DEFAULT '1',
  `AnalysisID` int(8) unsigned NOT NULL DEFAULT '0',
  `DetectorID` int(11) DEFAULT NULL,
  `BkgdDetectorID` double DEFAULT NULL,
  `Label` varchar(35) NOT NULL DEFAULT '',
  `NumCnts` smallint(5) unsigned NOT NULL DEFAULT '0',
  `NCyc` tinyint(4) DEFAULT NULL,
  `CycleStartIndexList` blob,
  `CycleStartIndexblob` blob,
  `BslnID` double DEFAULT NULL,
  `RatNumerator` tinyint(3) unsigned DEFAULT NULL,
  `RatDenominator` tinyint(3) unsigned DEFAULT NULL,
  `HallProbeAtStartOfRun` double DEFAULT NULL,
  `HallProbeAtEndOfRun` double DEFAULT NULL,
  PRIMARY KEY (`IsotopeID`),
  KEY `DetectorID` (`DetectorID`),
  KEY `AnalysisID` (`AnalysisID`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;



# Dump of table LoginSessionTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `LoginSessionTable`;

CREATE TABLE `LoginSessionTable` (
  `LoginSessionID` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `UserID` smallint(5) unsigned NOT NULL DEFAULT '0',
  `InitialRID` varchar(40) NOT NULL DEFAULT '',
  `SpecSysN` tinyint(3) unsigned NOT NULL DEFAULT '0',
  `SessionStart` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`LoginSessionID`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;

LOCK TABLES `LoginSessionTable` WRITE;
/*!40000 ALTER TABLE `LoginSessionTable` DISABLE KEYS */;

INSERT INTO `LoginSessionTable` (`LoginSessionID`, `UserID`, `InitialRID`, `SpecSysN`, `SessionStart`)
VALUES
	(1,0,'',0,'2014-01-28 21:55:18');

/*!40000 ALTER TABLE `LoginSessionTable` ENABLE KEYS */;
UNLOCK TABLES;


# Dump of table machinetable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `machinetable`;

CREATE TABLE `machinetable` (
  `SpecSysN` smallint(6) NOT NULL DEFAULT '0',
  `Label` varchar(40) DEFAULT NULL,
  PRIMARY KEY (`SpecSysN`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;



# Dump of table MassScanMeasurementsTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `MassScanMeasurementsTable`;

CREATE TABLE `MassScanMeasurementsTable` (
  `Counter` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `MassScanID` int(8) NOT NULL,
  `Label` char(20) NOT NULL,
  `Mass` float NOT NULL,
  `Signal` float NOT NULL,
  PRIMARY KEY (`Counter`),
  KEY `MassScanID` (`MassScanID`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;



# Dump of table MassScanTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `MassScanTable`;

CREATE TABLE `MassScanTable` (
  `ID` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `AnalysisID` int(8) NOT NULL,
  `MeasDateTime` datetime NOT NULL,
  `DetectorLabel` char(35) NOT NULL,
  `FileName` char(30) NOT NULL,
  `NPositions` tinyint(4) NOT NULL,
  `SignalArray` blob,
  `TimeArray` blob,
  PRIMARY KEY (`ID`),
  KEY `AnalysisID` (`AnalysisID`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;



# Dump of table MaterialTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `MaterialTable`;

CREATE TABLE `MaterialTable` (
  `ID` smallint(6) NOT NULL AUTO_INCREMENT,
  `Material` char(40) DEFAULT NULL,
  PRIMARY KEY (`ID`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;



# Dump of table molarweighttable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `molarweighttable`;

CREATE TABLE `molarweighttable` (
  `ID` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `Species` varchar(40) NOT NULL DEFAULT '',
  `AtomicWeight` double NOT NULL DEFAULT '0',
  PRIMARY KEY (`ID`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;



# Dump of table NobleRatioTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `NobleRatioTable`;

CREATE TABLE `NobleRatioTable` (
  `AnalysisID` int(8) unsigned NOT NULL,
  `Label` char(40) NOT NULL,
  `LastSaved` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `DataReductionSessionID` mediumint(8) unsigned DEFAULT NULL,
  `RatioUncor` double DEFAULT NULL,
  `RatioUncorEr` double DEFAULT NULL,
  `RatioCor` double DEFAULT NULL,
  `RatioCorEr` double DEFAULT NULL,
  `RatioSensCal` double DEFAULT NULL,
  `RatioSensCalEr` double DEFAULT NULL,
  `RatioVolCal` double DEFAULT NULL,
  `RatioVolCalEr` double DEFAULT NULL,
  `DeltaSensCalRatio` double DEFAULT NULL,
  `DeltaSensCalRatioEr` double DEFAULT NULL,
  `DeltaVolCalRatio` double DEFAULT NULL,
  `DeltaVolCalRatioEr` double DEFAULT NULL,
  KEY `AnalysisID` (`AnalysisID`),
  KEY `DataReductionSessionID` (`DataReductionSessionID`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;



# Dump of table pdptable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `pdptable`;

CREATE TABLE `pdptable` (
  `IsotopeID` int(10) unsigned NOT NULL DEFAULT '0',
  `LastSaved` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `DataReductionSessionID` mediumint(8) unsigned DEFAULT NULL,
  `PDPBlob` blob,
  KEY `IsotopeID` (`IsotopeID`),
  KEY `DataReductionSessionID` (`DataReductionSessionID`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;



# Dump of table PeakTimeTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `PeakTimeTable`;

CREATE TABLE `PeakTimeTable` (
  `Counter` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `LastSaved` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `IsotopeID` int(10) unsigned NOT NULL DEFAULT '0',
  `DataReductionSessionID` mediumint(8) unsigned DEFAULT NULL,
  `PeakTimeBlob` blob,
  `PeakNeverBslnCorBlob` blob,
  `RatioPtOriginBlob` blob,
  PRIMARY KEY (`Counter`),
  KEY `IsotopeID` (`IsotopeID`),
  KEY `DataReductionSessionID` (`DataReductionSessionID`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;



# Dump of table PipetteShotsTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `PipetteShotsTable`;

CREATE TABLE `PipetteShotsTable` (
  `Counter` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `EventDate` datetime NOT NULL,
  `AnalysisID` int(8) NOT NULL,
  `PipetteName` char(30) DEFAULT NULL,
  `LoadingNumber` smallint(5) unsigned NOT NULL,
  `AliquotNumber` int(10) unsigned NOT NULL,
  PRIMARY KEY (`Counter`),
  KEY `AnalysisID` (`AnalysisID`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;



# Dump of table PipetteTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `PipetteTable`;

CREATE TABLE `PipetteTable` (
  `PipetteName` char(30) DEFAULT NULL,
  `SpecSysN` smallint(6) NOT NULL,
  `CanNumber` smallint(5) unsigned NOT NULL,
  `DecayConst` double DEFAULT NULL,
  `LastAliquotNumber` int(10) unsigned NOT NULL,
  UNIQUE KEY `PipetteCanNumber` (`PipetteName`,`CanNumber`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;



# Dump of table potentialanalysispositiontable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `potentialanalysispositiontable`;

CREATE TABLE `potentialanalysispositiontable` (
  `RID` varchar(40) NOT NULL DEFAULT '',
  `SampleLoadingID` mediumint(8) unsigned NOT NULL DEFAULT '0',
  `PositionOrder` int(11) NOT NULL DEFAULT '0',
  `Hole` int(11) DEFAULT NULL,
  `X` double DEFAULT NULL,
  `Y` double DEFAULT NULL,
  KEY `RID` (`RID`),
  KEY `Hole` (`Hole`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;



# Dump of table PreferencesTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `PreferencesTable`;

CREATE TABLE `PreferencesTable` (
  `PreferencesSetID` int(11) NOT NULL DEFAULT '0',
  `EntirePrefFileBlob` blob NOT NULL,
  `SignalDisplayUnits` tinyint(4) NOT NULL DEFAULT '0',
  `SignalFormat` tinyint(4) NOT NULL,
  `Adjust36forH35Cl` enum('false','true') NOT NULL DEFAULT 'false',
  `AlwaysCalcWORatios` enum('false','true') NOT NULL DEFAULT 'false',
  `CalcPctRadToRadAndAtmOnly` enum('false','true') NOT NULL DEFAULT 'false',
  `ErrorCalcMethod` tinyint(4) NOT NULL DEFAULT '0',
  `ProbCutOff` double NOT NULL DEFAULT '0',
  `ErEnvSigmaFactor` double NOT NULL DEFAULT '0',
  `NFilterIter` tinyint(4) NOT NULL DEFAULT '0',
  `OutlierSigmaFactor` double NOT NULL DEFAULT '0',
  `DelPrior` enum('false','true') NOT NULL DEFAULT 'false',
  `AvePrior` enum('false','true') NOT NULL DEFAULT 'false',
  `DelOutliersAfterFit` enum('false','true') NOT NULL DEFAULT 'false',
  `CentTendType` tinyint(4) NOT NULL DEFAULT '0',
  `Fixed3739` double NOT NULL DEFAULT '0',
  `Fixed3739Val` double NOT NULL DEFAULT '0',
  `Fixed3739ValEr` double NOT NULL DEFAULT '0',
  `KAbund40` double NOT NULL DEFAULT '0',
  `KAbund40Er` double NOT NULL DEFAULT '0',
  `Lambda40Kepsilon` double NOT NULL DEFAULT '0',
  `Lambda40KepsilonEr` double NOT NULL DEFAULT '0',
  `Lambda40KBeta` double NOT NULL DEFAULT '0',
  `Lambda40KBetaEr` double NOT NULL DEFAULT '0',
  `LambdaAr37` double NOT NULL DEFAULT '0',
  `LambdaAr39` double NOT NULL DEFAULT '0',
  `LambdaCl36` double NOT NULL DEFAULT '0',
  `LambdaAr37Er` double NOT NULL DEFAULT '0',
  `LambdaAr39Er` double NOT NULL DEFAULT '0',
  `LambdaCl36Er` double NOT NULL DEFAULT '0',
  `A4036` double NOT NULL DEFAULT '0',
  `A4036Er` double NOT NULL DEFAULT '0',
  `A4038` double NOT NULL DEFAULT '0',
  `A4038Er` double NOT NULL DEFAULT '0',
  PRIMARY KEY (`PreferencesSetID`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;



# Dump of table projecttable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `projecttable`;

CREATE TABLE `projecttable` (
  `ProjectID` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `Project` varchar(40) NOT NULL DEFAULT '',
  `LastSaved` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `PrincipalInvestigator` varchar(40) NOT NULL DEFAULT '',
  `Collaborator` varchar(40) NOT NULL DEFAULT '',
  `Institution` varchar(40) NOT NULL DEFAULT '',
  `Note` blob NOT NULL,
  PRIMARY KEY (`ProjectID`),
  UNIQUE KEY `UniqueProjectPI` (`Project`,`PrincipalInvestigator`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;



# Dump of table ratiotable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `ratiotable`;

CREATE TABLE `ratiotable` (
  `AnalysisID` int(11) NOT NULL DEFAULT '0',
  `LastSaved` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `Label` varchar(35) DEFAULT NULL,
  `Iso` double DEFAULT NULL,
  `IsoEr` double DEFAULT NULL,
  `PkHtChangePct` double DEFAULT NULL,
  `Fit` tinyint(4) DEFAULT NULL,
  `GOF` double DEFAULT NULL,
  `RatNumerator` tinyint(3) unsigned DEFAULT NULL,
  `RatDenominator` tinyint(3) unsigned DEFAULT NULL
) ENGINE=MyISAM DEFAULT CHARSET=latin1;



# Dump of table ReservoirLoadingTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `ReservoirLoadingTable`;

CREATE TABLE `ReservoirLoadingTable` (
  `CanNumber` smallint(5) unsigned NOT NULL,
  `LoadingNumber` smallint(5) unsigned NOT NULL,
  `ReferenceIsotope` char(30) DEFAULT NULL,
  `ReferenceIsotopeMoles` double DEFAULT NULL,
  `ProportionOfOtherIsotopes` blob,
  UNIQUE KEY `CanLoading` (`CanNumber`,`LoadingNumber`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;



# Dump of table RunScriptTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `RunScriptTable`;

CREATE TABLE `RunScriptTable` (
  `RunScriptID` int(11) NOT NULL DEFAULT '0',
  `Label` varchar(40) NOT NULL DEFAULT '',
  `LastSaved` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `EventDate` timestamp NOT NULL DEFAULT '0000-00-00 00:00:00',
  `Note` text NOT NULL,
  `TheText` text NOT NULL,
  PRIMARY KEY (`RunScriptID`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;

LOCK TABLES `RunScriptTable` WRITE;
/*!40000 ALTER TABLE `RunScriptTable` DISABLE KEYS */;

INSERT INTO `RunScriptTable` (`RunScriptID`, `Label`, `LastSaved`, `EventDate`, `Note`, `TheText`)
VALUES
	(0,'','2014-01-28 21:55:18','0000-00-00 00:00:00','','');

/*!40000 ALTER TABLE `RunScriptTable` ENABLE KEYS */;
UNLOCK TABLES;


# Dump of table SampleHolderTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `SampleHolderTable`;

CREATE TABLE `SampleHolderTable` (
  `SampleHolder` varchar(40) NOT NULL DEFAULT '',
  `Type` smallint(6) NOT NULL,
  `Size` double NOT NULL,
  `PositionBlob` blob,
  `Bitmap` mediumblob,
  `BitmapNumberless` mediumblob,
  PRIMARY KEY (`SampleHolder`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;



# Dump of table sampleloadingtable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `sampleloadingtable`;

CREATE TABLE `sampleloadingtable` (
  `SampleLoadingID` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `SampleHolder` varchar(40) NOT NULL DEFAULT '',
  `SpecSysN` smallint(6) NOT NULL DEFAULT '0',
  `LoadingDate` datetime NOT NULL DEFAULT '0000-00-00 00:00:00',
  PRIMARY KEY (`SampleLoadingID`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;

LOCK TABLES `sampleloadingtable` WRITE;
/*!40000 ALTER TABLE `sampleloadingtable` DISABLE KEYS */;

INSERT INTO `sampleloadingtable` (`SampleLoadingID`, `SampleHolder`, `SpecSysN`, `LoadingDate`)
VALUES
	(1,'',0,'2014-01-28 21:55:18');

/*!40000 ALTER TABLE `sampleloadingtable` ENABLE KEYS */;
UNLOCK TABLES;


# Dump of table SampleTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `SampleTable`;

CREATE TABLE `SampleTable` (
  `SampleID` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  `LastSaved` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `Sample` varchar(40) NOT NULL DEFAULT '',
  `IGSN` char(9) DEFAULT NULL,
  `AlternateUserID` char(40) NOT NULL,
  `Project` varchar(40) NOT NULL DEFAULT '',
  `ProjectID` mediumint(8) unsigned NOT NULL DEFAULT '0',
  `CollectionDateTime` datetime NOT NULL,
  `Locality` varchar(40) NOT NULL DEFAULT '',
  `Coordinates` blob NOT NULL,
  `Latitude` char(15) NOT NULL,
  `Longitude` char(15) NOT NULL,
  `StratHeight` varchar(40) NOT NULL DEFAULT '',
  `Salinity` double NOT NULL,
  `Temperature` double NOT NULL,
  `Note` blob NOT NULL,
  `StratUnit` varchar(40) NOT NULL DEFAULT '',
  `Lithology` varchar(40) NOT NULL DEFAULT '',
  `ReferenceAge` double NOT NULL DEFAULT '0',
  `ReferenceAgeEr` double NOT NULL DEFAULT '0',
  PRIMARY KEY (`SampleID`),
  UNIQUE KEY `UniqueProjectSample` (`Sample`,`ProjectID`),
  KEY `Sample` (`Sample`),
  KEY `ProjectID` (`ProjectID`),
  KEY `Sample_2` (`Sample`),
  KEY `ProjectID_2` (`ProjectID`),
  KEY `Sample_3` (`Sample`),
  KEY `ProjectID_3` (`ProjectID`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;



# Dump of table SpecParamIonVantageTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `SpecParamIonVantageTable`;

CREATE TABLE `SpecParamIonVantageTable` (
  `ID` int(8) unsigned NOT NULL AUTO_INCREMENT,
  `AcceleratingVoltage` double NOT NULL,
  `ElectronVolts` double NOT NULL,
  `FilamentCurrent` double NOT NULL,
  `IonRepeller` double NOT NULL,
  `SourceCurrent` double NOT NULL,
  `SourceExtraction` double NOT NULL,
  `TrapCurrent` double NOT NULL,
  `YBias` double NOT NULL,
  `ZBias` double NOT NULL,
  PRIMARY KEY (`ID`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;



# Dump of table SpecParamNoblesseTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `SpecParamNoblesseTable`;

CREATE TABLE `SpecParamNoblesseTable` (
  `ID` int(8) unsigned NOT NULL AUTO_INCREMENT,
  `Cubic_1` double NOT NULL,
  `Cubic_2` double NOT NULL,
  `Deflect_IC0` double NOT NULL,
  `Deflect_IC1` double NOT NULL,
  `Deflect_IC2` double NOT NULL,
  `Deflect_IC3` double NOT NULL,
  `Delta_HP` double NOT NULL,
  `Delta_Z` double NOT NULL,
  `Disc_0` double NOT NULL,
  `Disc_1` double NOT NULL,
  `Disc_2` double NOT NULL,
  `Disc_3` double NOT NULL,
  `Filament_V` double NOT NULL,
  `Filter_IC0` double NOT NULL,
  `Filter_IC3` double NOT NULL,
  `Half_Plate_V` double NOT NULL,
  `IC_0` double NOT NULL,
  `IC_1` double NOT NULL,
  `IC_2` double NOT NULL,
  `IC_3` double NOT NULL,
  `Lin_1` double NOT NULL,
  `Lin_2` double NOT NULL,
  `Max_Power` double NOT NULL,
  `Q8_Cor` double NOT NULL,
  `Q9_Cor` double NOT NULL,
  `Quad_1` double NOT NULL,
  `Quad_2` double NOT NULL,
  `Repeller` double NOT NULL,
  `Source_HT` double NOT NULL,
  `Suppressor` double NOT NULL,
  `Trap` double NOT NULL,
  `Trap_Voltage` double NOT NULL,
  `Z_Lens` double NOT NULL,
  `Faraday_Defl` double NOT NULL,
  `IC0_Offset` double NOT NULL,
  `Deflect_1` double NOT NULL,
  `Deflect_2` double NOT NULL,
  `Filter_1` double NOT NULL,
  `Filter_2` double NOT NULL,
  PRIMARY KEY (`ID`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;



# Dump of table SpecParamThermoTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `SpecParamThermoTable`;

CREATE TABLE `SpecParamThermoTable` (
  `ID` int(8) unsigned NOT NULL AUTO_INCREMENT,
  `Trap_Voltage` double NOT NULL,
  `Electron_Energy` double NOT NULL,
  `Z_Symmetry` double NOT NULL,
  `Z_Focus` double NOT NULL,
  `Ion_Repeller` double NOT NULL,
  `Y_Symmetry` double NOT NULL,
  `Extraction_Lens` double NOT NULL,
  `HV` double NOT NULL,
  `H2_Steering` double NOT NULL,
  `H1_Steering` double NOT NULL,
  `Ax_Steering` double NOT NULL,
  `L1_Steering` double NOT NULL,
  `L2_Steering` double NOT NULL,
  `CDD_Steering` double NOT NULL,
  `CDD_Voltage` double NOT NULL,
  PRIMARY KEY (`ID`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;



# Dump of table SpecSensitivityTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `SpecSensitivityTable`;

CREATE TABLE `SpecSensitivityTable` (
  `RecordID` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `SpecSysN` smallint(6) NOT NULL DEFAULT '0',
  `LastSaved` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `DetectorTypeID` smallint(6) NOT NULL DEFAULT '0',
  `ExtractionLineConfigID` mediumint(8) unsigned DEFAULT NULL,
  `Parameter` double NOT NULL DEFAULT '0',
  `ParameterEr` double DEFAULT NULL,
  `Slope` double DEFAULT NULL,
  `ParameterBlob` blob,
  `StartingDate` datetime NOT NULL DEFAULT '0000-00-00 00:00:00',
  `UserID` smallint(5) unsigned NOT NULL DEFAULT '0',
  PRIMARY KEY (`RecordID`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;



# Dump of table SpecSetUpTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `SpecSetUpTable`;

CREATE TABLE `SpecSetUpTable` (
  `SpecSetUpID` int(11) NOT NULL DEFAULT '0',
  `Label` varchar(40) NOT NULL DEFAULT '',
  `LastSaved` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `EventDate` timestamp NOT NULL DEFAULT '0000-00-00 00:00:00',
  `Note` text NOT NULL,
  `TheText` text NOT NULL,
  PRIMARY KEY (`SpecSetUpID`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;



# Dump of table StandardsTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `StandardsTable`;

CREATE TABLE `StandardsTable` (
  `StandardID` smallint(5) unsigned NOT NULL AUTO_INCREMENT,
  `PreparationName` char(40) NOT NULL,
  `UnitName` char(40) NOT NULL,
  `MaterialID` smallint(5) unsigned NOT NULL,
  `Age` char(20) NOT NULL,
  `AgeEr` char(20) NOT NULL,
  `R` char(20) NOT NULL,
  `REr` char(20) NOT NULL,
  `K` char(20) NOT NULL,
  `KEr` char(20) NOT NULL,
  `Type` tinyint(4) NOT NULL,
  `Reference` blob NOT NULL,
  `Note` blob NOT NULL,
  PRIMARY KEY (`StandardID`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;



# Dump of table SynthesisTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `SynthesisTable`;

CREATE TABLE `SynthesisTable` (
  `Counter` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `GraphicsID` int(10) unsigned NOT NULL,
  `SynthesisType` tinyint(3) unsigned NOT NULL,
  `experimentidentifier` char(50) DEFAULT NULL,
  `experimentType` char(50) DEFAULT NULL,
  `sampleMaterial` char(50) DEFAULT NULL,
  `sampleTreatment` blob,
  `sampleWeight` double DEFAULT NULL,
  `extractionMethod` char(100) DEFAULT NULL,
  `steps` blob,
  `Rat40Rad39K` double DEFAULT NULL,
  `Rat40Rad39KSigma` double DEFAULT NULL,
  `age` double DEFAULT NULL,
  `ageSigma` double DEFAULT NULL,
  `AgeSigmaInternal` double DEFAULT NULL,
  `AgeSigmaExternal` double DEFAULT NULL,
  `KCaRatio` double DEFAULT NULL,
  `KCaRatioSigma` double DEFAULT NULL,
  `KClRatio` double DEFAULT NULL,
  `KClRatioSigma` double DEFAULT NULL,
  `MSWD` double DEFAULT NULL,
  `ErrorMagnification` double DEFAULT NULL,
  `n` smallint(6) DEFAULT NULL,
  `age_description` blob,
  `plateau_width` double DEFAULT NULL,
  `Ratio40Ar36Ar` double DEFAULT NULL,
  `Ratio40Ar36ArSigma` double DEFAULT NULL,
  `Convergence` double DEFAULT NULL,
  `Iterations` smallint(6) DEFAULT NULL,
  PRIMARY KEY (`Counter`),
  KEY `GraphicsID` (`GraphicsID`),
  KEY `experimentidentifier` (`experimentidentifier`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;



# Dump of table SysCkValuesTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `SysCkValuesTable`;

CREATE TABLE `SysCkValuesTable` (
  `AnalysisID` int(11) NOT NULL DEFAULT '0',
  `Label` varchar(35) DEFAULT NULL,
  `MeasValMin` float NOT NULL DEFAULT '0',
  `MeasValMax` float NOT NULL DEFAULT '0',
  `MeasValAve` float NOT NULL DEFAULT '0',
  `MeasValSD` float NOT NULL,
  `ValueTimeBlob` blob,
  KEY `Label` (`Label`),
  KEY `AnalysisID` (`AnalysisID`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;



# Dump of table SystemCkContLogTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `SystemCkContLogTable`;

CREATE TABLE `SystemCkContLogTable` (
  `Counter` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `SpecSysN` smallint(6) NOT NULL,
  `EventDate` datetime NOT NULL,
  `Furnace_Water` float DEFAULT NULL,
  `Lab_Temp` float DEFAULT NULL,
  `Lab_Humid` float DEFAULT NULL,
  `Pneumatics` float DEFAULT NULL,
  `Cold_Finger` float DEFAULT NULL,
  `Chiller` float DEFAULT NULL,
  `DB_Query_Test` float DEFAULT NULL,
  `DB_Query_Test2` float DEFAULT NULL,
  `MiniBoneFlag` float DEFAULT NULL,
  `Pipettes` float DEFAULT NULL,
  `PipetteFlag` float DEFAULT NULL,
  `ObamaPipetteFlag` float DEFAULT NULL,
  `PipetteBusyFlag` float DEFAULT NULL,
  `CO2BusyFlag` float DEFAULT NULL,
  `CO2PumpTimeFlag` float DEFAULT NULL,
  PRIMARY KEY (`Counter`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;



# Dump of table WaterExtractionTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `WaterExtractionTable`;

CREATE TABLE `WaterExtractionTable` (
  `ExtrNo` int(10) unsigned NOT NULL,
  `LastSaved` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `ExtrType` char(40) DEFAULT NULL,
  `LDEOSampleID` bigint(20) unsigned DEFAULT NULL,
  `AddID` blob,
  `ExtrDate` date DEFAULT NULL,
  `HeWeight` double DEFAULT NULL,
  `TrWeight` double DEFAULT NULL,
  `Comment` blob,
  `Branch` int(10) unsigned DEFAULT NULL,
  `Session` int(10) unsigned DEFAULT NULL,
  `Kind` char(40) DEFAULT NULL,
  `HeAndOrTr` char(40) DEFAULT NULL,
  `CuFull` double DEFAULT NULL,
  `CuEmpty` double DEFAULT NULL,
  `TrFull` double DEFAULT NULL,
  `TrEmpty` double DEFAULT NULL,
  `Channel` char(40) DEFAULT NULL,
  `InitLeakP` double DEFAULT NULL,
  `Ampule` char(40) DEFAULT NULL,
  `StartTime` datetime DEFAULT NULL,
  `HeatM` char(40) DEFAULT NULL,
  `TimeHeatM` datetime DEFAULT NULL,
  `HeatE` char(40) DEFAULT NULL,
  `TimeHeatE` datetime DEFAULT NULL,
  `EndTime` datetime DEFAULT NULL,
  `LeakP` double DEFAULT NULL,
  `BulbOutP` double DEFAULT NULL,
  `TrSealP` char(40) DEFAULT NULL,
  `status` char(40) DEFAULT NULL,
  `Operator` char(40) DEFAULT NULL,
  `PageNo` int(10) unsigned DEFAULT NULL,
  `LabelNo` int(10) unsigned DEFAULT NULL,
  `BottleFull` double DEFAULT NULL,
  `BottleEmpty` double DEFAULT NULL,
  `BulbFull` double DEFAULT NULL,
  `BulbEmpty` double DEFAULT NULL,
  `TrapBlocked` char(40) DEFAULT NULL,
  `SealingTime` datetime DEFAULT NULL,
  `InitialP` double DEFAULT NULL,
  `BulbBotAttP` double DEFAULT NULL,
  `DegNonCapValesP` double DEFAULT NULL,
  `DegCapValesP` double DEFAULT NULL,
  `SmallBig` char(40) DEFAULT NULL,
  `EndHeadspace` datetime DEFAULT NULL,
  `Initial2` char(40) DEFAULT NULL,
  `BulbBotAttP2` char(40) DEFAULT NULL,
  `DegNonCapValesP2` double DEFAULT NULL,
  `DegCapVales2` double DEFAULT NULL,
  PRIMARY KEY (`ExtrNo`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;




/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;
/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
