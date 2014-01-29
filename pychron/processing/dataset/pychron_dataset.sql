# ************************************************************
# Sequel Pro SQL dump
# Version 4096
#
# http://www.sequelpro.com/
# http://code.google.com/p/sequel-pro/
#
# Host: 127.0.0.1 (MySQL 5.5.20-log)
# Database: pychrondata_dev
# Generation Time: 2014-01-28 22:12:23 +0000
# ************************************************************


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;


# Dump of table alembic_version
# ------------------------------------------------------------

DROP TABLE IF EXISTS `alembic_version`;

CREATE TABLE `alembic_version` (
  `version_num` varchar(32) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;



# Dump of table association
# ------------------------------------------------------------

DROP TABLE IF EXISTS `association`;

CREATE TABLE `association` (
  `project_id` int(11) DEFAULT NULL,
  `user_id` int(11) DEFAULT NULL,
  KEY `project_id` (`project_id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `association_ibfk_1` FOREIGN KEY (`project_id`) REFERENCES `gen_ProjectTable` (`id`),
  CONSTRAINT `association_ibfk_2` FOREIGN KEY (`user_id`) REFERENCES `gen_UserTable` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;



# Dump of table dash_DeviceTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `dash_DeviceTable`;

CREATE TABLE `dash_DeviceTable` (
  `name` varchar(80) DEFAULT NULL,
  `scan_fmt` varchar(32) DEFAULT NULL,
  `scan_meta` blob,
  `scan_blob` blob,
  `time_table_id` int(11) DEFAULT NULL,
  `id` int(11) NOT NULL AUTO_INCREMENT,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;



# Dump of table dash_TimeTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `dash_TimeTable`;

CREATE TABLE `dash_TimeTable` (
  `start` datetime DEFAULT NULL,
  `end` datetime DEFAULT NULL,
  `id` int(11) NOT NULL AUTO_INCREMENT,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;



# Dump of table flux_FluxTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `flux_FluxTable`;

CREATE TABLE `flux_FluxTable` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `j` float DEFAULT NULL,
  `j_err` float DEFAULT NULL,
  `history_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `history_id` (`history_id`),
  CONSTRAINT `flux_fluxtable_ibfk_1` FOREIGN KEY (`history_id`) REFERENCES `flux_HistoryTable` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;



# Dump of table flux_HistoryTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `flux_HistoryTable`;

CREATE TABLE `flux_HistoryTable` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `irradiation_position_id` int(11) DEFAULT NULL,
  `create_date` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `irradiation_position_id` (`irradiation_position_id`),
  CONSTRAINT `flux_historytable_ibfk_1` FOREIGN KEY (`irradiation_position_id`) REFERENCES `irrad_PositionTable` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;



# Dump of table flux_MonitorTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `flux_MonitorTable`;

CREATE TABLE `flux_MonitorTable` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(80) DEFAULT NULL,
  `decay_constant` float DEFAULT NULL,
  `decay_constant_err` float DEFAULT NULL,
  `age` float DEFAULT NULL,
  `age_err` float DEFAULT NULL,
  `sample_id` int(11) DEFAULT NULL,
  `ref` varchar(140) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `sample_id` (`sample_id`),
  CONSTRAINT `flux_monitortable_ibfk_1` FOREIGN KEY (`sample_id`) REFERENCES `gen_SampleTable` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;



# Dump of table gen_AnalysisTypeTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `gen_AnalysisTypeTable`;

CREATE TABLE `gen_AnalysisTypeTable` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(80) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;



# Dump of table gen_DetectorTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `gen_DetectorTable`;

CREATE TABLE `gen_DetectorTable` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(80) DEFAULT NULL,
  `kind` varchar(40) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;



# Dump of table gen_ExtractionDeviceTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `gen_ExtractionDeviceTable`;

CREATE TABLE `gen_ExtractionDeviceTable` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(80) DEFAULT NULL,
  `kind` varchar(40) DEFAULT NULL,
  `make` varchar(40) DEFAULT NULL,
  `model` varchar(40) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;



# Dump of table gen_ImportTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `gen_ImportTable`;

CREATE TABLE `gen_ImportTable` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `date` datetime DEFAULT NULL,
  `user` varchar(40) DEFAULT NULL,
  `source` varchar(40) DEFAULT NULL,
  `source_host` varchar(40) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;



# Dump of table gen_LabTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `gen_LabTable`;

CREATE TABLE `gen_LabTable` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `identifier` varchar(40) DEFAULT NULL,
  `sample_id` int(11) DEFAULT NULL,
  `irradiation_id` int(11) DEFAULT NULL,
  `selected_flux_id` int(11) DEFAULT NULL,
  `note` varchar(140) DEFAULT NULL,
  `selected_interpreted_age_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `sample_id` (`sample_id`),
  KEY `irradiation_id` (`irradiation_id`),
  KEY `selected_flux_id` (`selected_flux_id`),
  KEY `selected_interpreted_age_id` (`selected_interpreted_age_id`),
  CONSTRAINT `gen_labtable_ibfk_1` FOREIGN KEY (`sample_id`) REFERENCES `gen_SampleTable` (`id`),
  CONSTRAINT `gen_labtable_ibfk_2` FOREIGN KEY (`irradiation_id`) REFERENCES `irrad_PositionTable` (`id`),
  CONSTRAINT `gen_labtable_ibfk_3` FOREIGN KEY (`selected_flux_id`) REFERENCES `flux_HistoryTable` (`id`),
  CONSTRAINT `gen_labtable_ibfk_4` FOREIGN KEY (`selected_interpreted_age_id`) REFERENCES `proc_InterpretedAgeHistoryTable` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;



# Dump of table gen_LoadHolderTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `gen_LoadHolderTable`;

CREATE TABLE `gen_LoadHolderTable` (
  `name` varchar(80) NOT NULL,
  `geometry` blob,
  PRIMARY KEY (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;



# Dump of table gen_MassSpectrometerTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `gen_MassSpectrometerTable`;

CREATE TABLE `gen_MassSpectrometerTable` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(80) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;



# Dump of table gen_MaterialTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `gen_MaterialTable`;

CREATE TABLE `gen_MaterialTable` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(80) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;



# Dump of table gen_MolecularWeightTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `gen_MolecularWeightTable`;

CREATE TABLE `gen_MolecularWeightTable` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(80) DEFAULT NULL,
  `mass` float DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;



# Dump of table gen_ProjectTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `gen_ProjectTable`;

CREATE TABLE `gen_ProjectTable` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(80) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;



# Dump of table gen_SampleTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `gen_SampleTable`;

CREATE TABLE `gen_SampleTable` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(80) DEFAULT NULL,
  `alt_name` varchar(80) DEFAULT NULL,
  `material_id` int(11) DEFAULT NULL,
  `project_id` int(11) DEFAULT NULL,
  `location` varchar(80) DEFAULT NULL,
  `lat` double DEFAULT NULL,
  `long` double DEFAULT NULL,
  `elevation` float DEFAULT NULL,
  `igsn` char(9) DEFAULT NULL,
  `note` blob,
  `lithology` varchar(80) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `material_id` (`material_id`),
  KEY `project_id` (`project_id`),
  CONSTRAINT `gen_sampletable_ibfk_1` FOREIGN KEY (`material_id`) REFERENCES `gen_MaterialTable` (`id`),
  CONSTRAINT `gen_sampletable_ibfk_2` FOREIGN KEY (`project_id`) REFERENCES `gen_ProjectTable` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;



# Dump of table gen_SensitivityTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `gen_SensitivityTable`;

CREATE TABLE `gen_SensitivityTable` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `mass_spectrometer_id` int(11) DEFAULT NULL,
  `sensitivity` double DEFAULT NULL,
  `create_date` datetime DEFAULT NULL,
  `user` varchar(40) DEFAULT NULL,
  `note` blob,
  PRIMARY KEY (`id`),
  KEY `mass_spectrometer_id` (`mass_spectrometer_id`),
  CONSTRAINT `gen_sensitivitytable_ibfk_1` FOREIGN KEY (`mass_spectrometer_id`) REFERENCES `gen_MassSpectrometerTable` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;



# Dump of table gen_UserTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `gen_UserTable`;

CREATE TABLE `gen_UserTable` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(80) DEFAULT NULL,
  `password` varchar(80) DEFAULT NULL,
  `salt` varchar(80) DEFAULT NULL,
  `max_allowable_runs` int(11) DEFAULT NULL,
  `can_edit_scripts` tinyint(1) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;



# Dump of table irrad_ChronologyTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `irrad_ChronologyTable`;

CREATE TABLE `irrad_ChronologyTable` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `chronology` blob,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;



# Dump of table irrad_HolderTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `irrad_HolderTable`;

CREATE TABLE `irrad_HolderTable` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(80) DEFAULT NULL,
  `geometry` blob,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;



# Dump of table irrad_IrradiationTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `irrad_IrradiationTable`;

CREATE TABLE `irrad_IrradiationTable` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(80) DEFAULT NULL,
  `irradiation_production_id` int(11) DEFAULT NULL,
  `irradiation_chronology_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `irradiation_production_id` (`irradiation_production_id`),
  KEY `irradiation_chronology_id` (`irradiation_chronology_id`),
  CONSTRAINT `irrad_irradiationtable_ibfk_1` FOREIGN KEY (`irradiation_production_id`) REFERENCES `irrad_ProductionTable` (`id`),
  CONSTRAINT `irrad_irradiationtable_ibfk_2` FOREIGN KEY (`irradiation_chronology_id`) REFERENCES `irrad_ChronologyTable` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;



# Dump of table irrad_LevelTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `irrad_LevelTable`;

CREATE TABLE `irrad_LevelTable` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(80) DEFAULT NULL,
  `z` float DEFAULT NULL,
  `holder_id` int(11) DEFAULT NULL,
  `irradiation_id` int(11) DEFAULT NULL,
  `production_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `holder_id` (`holder_id`),
  KEY `irradiation_id` (`irradiation_id`),
  KEY `production_id` (`production_id`),
  CONSTRAINT `irrad_leveltable_ibfk_1` FOREIGN KEY (`holder_id`) REFERENCES `irrad_HolderTable` (`id`),
  CONSTRAINT `irrad_leveltable_ibfk_2` FOREIGN KEY (`irradiation_id`) REFERENCES `irrad_IrradiationTable` (`id`),
  CONSTRAINT `irrad_leveltable_ibfk_3` FOREIGN KEY (`production_id`) REFERENCES `irrad_ProductionTable` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;



# Dump of table irrad_PositionTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `irrad_PositionTable`;

CREATE TABLE `irrad_PositionTable` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `level_id` int(11) DEFAULT NULL,
  `position` int(11) DEFAULT NULL,
  `weight` float DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `level_id` (`level_id`),
  CONSTRAINT `irrad_positiontable_ibfk_1` FOREIGN KEY (`level_id`) REFERENCES `irrad_LevelTable` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;



# Dump of table irrad_ProductionTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `irrad_ProductionTable`;

CREATE TABLE `irrad_ProductionTable` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(80) DEFAULT NULL,
  `K4039` float DEFAULT NULL,
  `K4039_err` float DEFAULT NULL,
  `K3839` float DEFAULT NULL,
  `K3839_err` float DEFAULT NULL,
  `K3739` float DEFAULT NULL,
  `K3739_err` float DEFAULT NULL,
  `Ca3937` float DEFAULT NULL,
  `Ca3937_err` float DEFAULT NULL,
  `Ca3837` float DEFAULT NULL,
  `Ca3837_err` float DEFAULT NULL,
  `Ca3637` float DEFAULT NULL,
  `Ca3637_err` float DEFAULT NULL,
  `Cl3638` float DEFAULT NULL,
  `Cl3638_err` float DEFAULT NULL,
  `Ca_K` float DEFAULT NULL,
  `Ca_K_err` float DEFAULT NULL,
  `Cl_K` float DEFAULT NULL,
  `Cl_K_err` float DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;



# Dump of table loading_LoadTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `loading_LoadTable`;

CREATE TABLE `loading_LoadTable` (
  `name` varchar(80) NOT NULL,
  `create_date` datetime DEFAULT NULL,
  `holder` varchar(80) DEFAULT NULL,
  PRIMARY KEY (`name`),
  KEY `holder` (`holder`),
  CONSTRAINT `loading_loadtable_ibfk_1` FOREIGN KEY (`holder`) REFERENCES `gen_LoadHolderTable` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;



# Dump of table loading_PositionsTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `loading_PositionsTable`;

CREATE TABLE `loading_PositionsTable` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `load_identifier` varchar(80) DEFAULT NULL,
  `lab_identifier` int(11) DEFAULT NULL,
  `position` int(11) DEFAULT NULL,
  `weight` float DEFAULT NULL,
  `note` blob,
  PRIMARY KEY (`id`),
  KEY `load_identifier` (`load_identifier`),
  KEY `lab_identifier` (`lab_identifier`),
  CONSTRAINT `loading_positionstable_ibfk_1` FOREIGN KEY (`load_identifier`) REFERENCES `loading_LoadTable` (`name`),
  CONSTRAINT `loading_positionstable_ibfk_2` FOREIGN KEY (`lab_identifier`) REFERENCES `gen_LabTable` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;



# Dump of table meas_AnalysisTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `meas_AnalysisTable`;

CREATE TABLE `meas_AnalysisTable` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `lab_id` int(11) DEFAULT NULL,
  `extraction_id` int(11) DEFAULT NULL,
  `measurement_id` int(11) DEFAULT NULL,
  `experiment_id` int(11) DEFAULT NULL,
  `import_id` int(11) DEFAULT NULL,
  `user_id` int(11) DEFAULT NULL,
  `uuid` varchar(40) DEFAULT NULL,
  `analysis_timestamp` datetime DEFAULT NULL,
  `endtime` time DEFAULT NULL,
  `status` int(11) DEFAULT NULL,
  `aliquot` int(11) DEFAULT NULL,
  `step` varchar(10) DEFAULT NULL,
  `comment` blob,
  `tag` varchar(40) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `lab_id` (`lab_id`),
  KEY `extraction_id` (`extraction_id`),
  KEY `measurement_id` (`measurement_id`),
  KEY `experiment_id` (`experiment_id`),
  KEY `import_id` (`import_id`),
  KEY `user_id` (`user_id`),
  KEY `tag` (`tag`),
  CONSTRAINT `meas_analysistable_ibfk_1` FOREIGN KEY (`lab_id`) REFERENCES `gen_LabTable` (`id`),
  CONSTRAINT `meas_analysistable_ibfk_2` FOREIGN KEY (`extraction_id`) REFERENCES `meas_ExtractionTable` (`id`),
  CONSTRAINT `meas_analysistable_ibfk_3` FOREIGN KEY (`measurement_id`) REFERENCES `meas_MeasurementTable` (`id`),
  CONSTRAINT `meas_analysistable_ibfk_4` FOREIGN KEY (`experiment_id`) REFERENCES `meas_ExperimentTable` (`id`),
  CONSTRAINT `meas_analysistable_ibfk_5` FOREIGN KEY (`import_id`) REFERENCES `gen_ImportTable` (`id`),
  CONSTRAINT `meas_analysistable_ibfk_6` FOREIGN KEY (`user_id`) REFERENCES `gen_UserTable` (`id`),
  CONSTRAINT `meas_analysistable_ibfk_7` FOREIGN KEY (`tag`) REFERENCES `proc_TagTable` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;



# Dump of table meas_ExperimentTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `meas_ExperimentTable`;

CREATE TABLE `meas_ExperimentTable` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(80) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;



# Dump of table meas_ExtractionTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `meas_ExtractionTable`;

CREATE TABLE `meas_ExtractionTable` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `extract_value` float DEFAULT NULL,
  `extract_duration` float DEFAULT NULL,
  `cleanup_duration` float DEFAULT NULL,
  `extract_units` varchar(5) DEFAULT NULL,
  `weight` float DEFAULT NULL,
  `sensitivity_multiplier` float DEFAULT NULL,
  `is_degas` tinyint(1) DEFAULT NULL,
  `beam_diameter` float DEFAULT NULL,
  `pattern` varchar(100) DEFAULT NULL,
  `ramp_rate` float DEFAULT NULL,
  `ramp_duration` float DEFAULT NULL,
  `mask_position` float DEFAULT NULL,
  `mask_name` varchar(100) DEFAULT NULL,
  `attenuator` float DEFAULT NULL,
  `reprate` float DEFAULT NULL,
  `sensitivity_id` int(11) DEFAULT NULL,
  `extract_device_id` int(11) DEFAULT NULL,
  `script_id` int(11) DEFAULT NULL,
  `experiment_blob_id` int(11) DEFAULT NULL,
  `image_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `sensitivity_id` (`sensitivity_id`),
  KEY `extract_device_id` (`extract_device_id`),
  KEY `script_id` (`script_id`),
  KEY `experiment_blob_id` (`experiment_blob_id`),
  KEY `image_id` (`image_id`),
  CONSTRAINT `meas_extractiontable_ibfk_1` FOREIGN KEY (`sensitivity_id`) REFERENCES `gen_SensitivityTable` (`id`),
  CONSTRAINT `meas_extractiontable_ibfk_2` FOREIGN KEY (`extract_device_id`) REFERENCES `gen_ExtractionDeviceTable` (`id`),
  CONSTRAINT `meas_extractiontable_ibfk_3` FOREIGN KEY (`script_id`) REFERENCES `meas_ScriptTable` (`id`),
  CONSTRAINT `meas_extractiontable_ibfk_4` FOREIGN KEY (`experiment_blob_id`) REFERENCES `meas_ScriptTable` (`id`),
  CONSTRAINT `meas_extractiontable_ibfk_5` FOREIGN KEY (`image_id`) REFERENCES `med_ImageTable` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;



# Dump of table meas_IsotopeTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `meas_IsotopeTable`;

CREATE TABLE `meas_IsotopeTable` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `molecular_weight_id` int(11) DEFAULT NULL,
  `analysis_id` int(11) DEFAULT NULL,
  `detector_id` int(11) DEFAULT NULL,
  `kind` varchar(40) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `molecular_weight_id` (`molecular_weight_id`),
  KEY `analysis_id` (`analysis_id`),
  KEY `detector_id` (`detector_id`),
  CONSTRAINT `meas_isotopetable_ibfk_1` FOREIGN KEY (`molecular_weight_id`) REFERENCES `gen_MolecularWeightTable` (`id`),
  CONSTRAINT `meas_isotopetable_ibfk_2` FOREIGN KEY (`analysis_id`) REFERENCES `meas_AnalysisTable` (`id`),
  CONSTRAINT `meas_isotopetable_ibfk_3` FOREIGN KEY (`detector_id`) REFERENCES `gen_DetectorTable` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;



# Dump of table meas_MeasurementTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `meas_MeasurementTable`;

CREATE TABLE `meas_MeasurementTable` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `mass_spectrometer_id` int(11) DEFAULT NULL,
  `analysis_type_id` int(11) DEFAULT NULL,
  `spectrometer_parameters_id` int(11) DEFAULT NULL,
  `script_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `mass_spectrometer_id` (`mass_spectrometer_id`),
  KEY `analysis_type_id` (`analysis_type_id`),
  KEY `spectrometer_parameters_id` (`spectrometer_parameters_id`),
  KEY `script_id` (`script_id`),
  CONSTRAINT `meas_measurementtable_ibfk_1` FOREIGN KEY (`mass_spectrometer_id`) REFERENCES `gen_MassSpectrometerTable` (`id`),
  CONSTRAINT `meas_measurementtable_ibfk_2` FOREIGN KEY (`analysis_type_id`) REFERENCES `gen_AnalysisTypeTable` (`id`),
  CONSTRAINT `meas_measurementtable_ibfk_3` FOREIGN KEY (`spectrometer_parameters_id`) REFERENCES `meas_SpectrometerParametersTable` (`id`),
  CONSTRAINT `meas_measurementtable_ibfk_4` FOREIGN KEY (`script_id`) REFERENCES `meas_ScriptTable` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;



# Dump of table meas_MonitorTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `meas_MonitorTable`;

CREATE TABLE `meas_MonitorTable` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(80) DEFAULT NULL,
  `data` blob,
  `parameter` varchar(40) DEFAULT NULL,
  `criterion` varchar(40) DEFAULT NULL,
  `comparator` varchar(40) DEFAULT NULL,
  `action` varchar(40) DEFAULT NULL,
  `tripped` tinyint(1) DEFAULT NULL,
  `analysis_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `analysis_id` (`analysis_id`),
  CONSTRAINT `meas_monitortable_ibfk_1` FOREIGN KEY (`analysis_id`) REFERENCES `meas_AnalysisTable` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;



# Dump of table meas_PeakCenterTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `meas_PeakCenterTable`;

CREATE TABLE `meas_PeakCenterTable` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `center` double DEFAULT NULL,
  `points` blob,
  `analysis_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `analysis_id` (`analysis_id`),
  CONSTRAINT `meas_peakcentertable_ibfk_1` FOREIGN KEY (`analysis_id`) REFERENCES `meas_AnalysisTable` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;



# Dump of table meas_PositionTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `meas_PositionTable`;

CREATE TABLE `meas_PositionTable` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `position` int(11) DEFAULT NULL,
  `x` float DEFAULT NULL,
  `y` float DEFAULT NULL,
  `z` float DEFAULT NULL,
  `is_degas` tinyint(1) DEFAULT NULL,
  `extraction_id` int(11) DEFAULT NULL,
  `load_identifier` varchar(80) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `extraction_id` (`extraction_id`),
  KEY `load_identifier` (`load_identifier`),
  CONSTRAINT `meas_positiontable_ibfk_1` FOREIGN KEY (`extraction_id`) REFERENCES `meas_ExtractionTable` (`id`),
  CONSTRAINT `meas_positiontable_ibfk_2` FOREIGN KEY (`load_identifier`) REFERENCES `loading_LoadTable` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;



# Dump of table meas_ScriptTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `meas_ScriptTable`;

CREATE TABLE `meas_ScriptTable` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(80) DEFAULT NULL,
  `hash` varchar(32) DEFAULT NULL,
  `blob` blob,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;



# Dump of table meas_SignalTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `meas_SignalTable`;

CREATE TABLE `meas_SignalTable` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `data` blob,
  `isotope_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `isotope_id` (`isotope_id`),
  CONSTRAINT `meas_signaltable_ibfk_1` FOREIGN KEY (`isotope_id`) REFERENCES `meas_IsotopeTable` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;



# Dump of table meas_SpectrometerDeflectionsTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `meas_SpectrometerDeflectionsTable`;

CREATE TABLE `meas_SpectrometerDeflectionsTable` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `detector_id` int(11) DEFAULT NULL,
  `measurement_id` int(11) DEFAULT NULL,
  `deflection` float DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `detector_id` (`detector_id`),
  KEY `measurement_id` (`measurement_id`),
  CONSTRAINT `meas_spectrometerdeflectionstable_ibfk_1` FOREIGN KEY (`detector_id`) REFERENCES `gen_DetectorTable` (`id`),
  CONSTRAINT `meas_spectrometerdeflectionstable_ibfk_2` FOREIGN KEY (`measurement_id`) REFERENCES `meas_MeasurementTable` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;



# Dump of table meas_SpectrometerParametersTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `meas_SpectrometerParametersTable`;

CREATE TABLE `meas_SpectrometerParametersTable` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `extraction_lens` float DEFAULT NULL,
  `ysymmetry` float DEFAULT NULL,
  `zsymmetry` float DEFAULT NULL,
  `zfocus` float DEFAULT NULL,
  `hash` varchar(32) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;



# Dump of table med_ImageTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `med_ImageTable`;

CREATE TABLE `med_ImageTable` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(80) DEFAULT NULL,
  `create_date` datetime DEFAULT NULL,
  `image` blob,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;



# Dump of table med_SnapshotTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `med_SnapshotTable`;

CREATE TABLE `med_SnapshotTable` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `path` varchar(200) DEFAULT NULL,
  `create_date` datetime DEFAULT NULL,
  `image` blob,
  `extraction_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `extraction_id` (`extraction_id`),
  CONSTRAINT `med_snapshottable_ibfk_1` FOREIGN KEY (`extraction_id`) REFERENCES `meas_ExtractionTable` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;



# Dump of table proc_ArArHistoryTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `proc_ArArHistoryTable`;

CREATE TABLE `proc_ArArHistoryTable` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `create_date` datetime DEFAULT NULL,
  `user` varchar(40) DEFAULT NULL,
  `analysis_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `analysis_id` (`analysis_id`),
  CONSTRAINT `proc_ararhistorytable_ibfk_1` FOREIGN KEY (`analysis_id`) REFERENCES `meas_AnalysisTable` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;



# Dump of table proc_ArArTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `proc_ArArTable`;

CREATE TABLE `proc_ArArTable` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `history_id` int(11) DEFAULT NULL,
  `age` float DEFAULT NULL,
  `age_err` float DEFAULT NULL,
  `age_err_wo_j` float DEFAULT NULL,
  `k39` float DEFAULT NULL,
  `k39_err` float DEFAULT NULL,
  `ca37` float DEFAULT NULL,
  `ca37_err` float DEFAULT NULL,
  `cl36` float DEFAULT NULL,
  `cl36_err` float DEFAULT NULL,
  `Ar40` float DEFAULT NULL,
  `Ar40_err` float DEFAULT NULL,
  `Ar39` float DEFAULT NULL,
  `Ar39_err` float DEFAULT NULL,
  `Ar38` float DEFAULT NULL,
  `Ar38_err` float DEFAULT NULL,
  `Ar37` float DEFAULT NULL,
  `Ar37_err` float DEFAULT NULL,
  `Ar36` float DEFAULT NULL,
  `Ar36_err` float DEFAULT NULL,
  `rad40` float DEFAULT NULL,
  `rad40_err` float DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `history_id` (`history_id`),
  CONSTRAINT `proc_arartable_ibfk_1` FOREIGN KEY (`history_id`) REFERENCES `proc_ArArHistoryTable` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;



# Dump of table proc_BackgroundsHistoryTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `proc_BackgroundsHistoryTable`;

CREATE TABLE `proc_BackgroundsHistoryTable` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `create_date` datetime DEFAULT NULL,
  `user` varchar(40) DEFAULT NULL,
  `analysis_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `analysis_id` (`analysis_id`),
  CONSTRAINT `proc_backgroundshistorytable_ibfk_1` FOREIGN KEY (`analysis_id`) REFERENCES `meas_AnalysisTable` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;



# Dump of table proc_BackgroundsSetTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `proc_BackgroundsSetTable`;

CREATE TABLE `proc_BackgroundsSetTable` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `backgrounds_id` int(11) DEFAULT NULL,
  `background_analysis_id` int(11) DEFAULT NULL,
  `set_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `backgrounds_id` (`backgrounds_id`),
  KEY `background_analysis_id` (`background_analysis_id`),
  CONSTRAINT `proc_backgroundssettable_ibfk_1` FOREIGN KEY (`backgrounds_id`) REFERENCES `proc_BackgroundsTable` (`id`),
  CONSTRAINT `proc_backgroundssettable_ibfk_2` FOREIGN KEY (`background_analysis_id`) REFERENCES `meas_AnalysisTable` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;



# Dump of table proc_BackgroundsTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `proc_BackgroundsTable`;

CREATE TABLE `proc_BackgroundsTable` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `history_id` int(11) DEFAULT NULL,
  `user_value` float DEFAULT NULL,
  `user_error` float DEFAULT NULL,
  `use_set` tinyint(1) DEFAULT NULL,
  `isotope` varchar(40) DEFAULT NULL,
  `fit` varchar(40) DEFAULT NULL,
  `set_id` int(11) DEFAULT NULL,
  `error_type` varchar(40) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `history_id` (`history_id`),
  CONSTRAINT `proc_backgroundstable_ibfk_1` FOREIGN KEY (`history_id`) REFERENCES `proc_BackgroundsHistoryTable` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;



# Dump of table proc_BlanksHistoryTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `proc_BlanksHistoryTable`;

CREATE TABLE `proc_BlanksHistoryTable` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `create_date` datetime DEFAULT NULL,
  `user` varchar(40) DEFAULT NULL,
  `analysis_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `analysis_id` (`analysis_id`),
  CONSTRAINT `proc_blankshistorytable_ibfk_1` FOREIGN KEY (`analysis_id`) REFERENCES `meas_AnalysisTable` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;



# Dump of table proc_BlanksSetTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `proc_BlanksSetTable`;

CREATE TABLE `proc_BlanksSetTable` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `blanks_id` int(11) DEFAULT NULL,
  `blank_analysis_id` int(11) DEFAULT NULL,
  `set_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `blanks_id` (`blanks_id`),
  KEY `blank_analysis_id` (`blank_analysis_id`),
  CONSTRAINT `proc_blankssettable_ibfk_1` FOREIGN KEY (`blanks_id`) REFERENCES `proc_BlanksTable` (`id`),
  CONSTRAINT `proc_blankssettable_ibfk_2` FOREIGN KEY (`blank_analysis_id`) REFERENCES `meas_AnalysisTable` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;



# Dump of table proc_BlanksTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `proc_BlanksTable`;

CREATE TABLE `proc_BlanksTable` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `history_id` int(11) DEFAULT NULL,
  `user_value` float DEFAULT NULL,
  `user_error` float DEFAULT NULL,
  `use_set` tinyint(1) DEFAULT NULL,
  `isotope` varchar(40) DEFAULT NULL,
  `fit` varchar(40) DEFAULT NULL,
  `set_id` int(11) DEFAULT NULL,
  `error_type` varchar(40) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `history_id` (`history_id`),
  CONSTRAINT `proc_blankstable_ibfk_1` FOREIGN KEY (`history_id`) REFERENCES `proc_BlanksHistoryTable` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;



# Dump of table proc_DetectorIntercalibrationHistoryTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `proc_DetectorIntercalibrationHistoryTable`;

CREATE TABLE `proc_DetectorIntercalibrationHistoryTable` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `create_date` datetime DEFAULT NULL,
  `user` varchar(40) DEFAULT NULL,
  `analysis_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `analysis_id` (`analysis_id`),
  CONSTRAINT `proc_detectorintercalibrationhistorytable_ibfk_1` FOREIGN KEY (`analysis_id`) REFERENCES `meas_AnalysisTable` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;



# Dump of table proc_DetectorIntercalibrationSetTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `proc_DetectorIntercalibrationSetTable`;

CREATE TABLE `proc_DetectorIntercalibrationSetTable` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `intercalibration_id` int(11) DEFAULT NULL,
  `ic_analysis_id` int(11) DEFAULT NULL,
  `set_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `intercalibration_id` (`intercalibration_id`),
  KEY `ic_analysis_id` (`ic_analysis_id`),
  CONSTRAINT `proc_detectorintercalibrationsettable_ibfk_1` FOREIGN KEY (`intercalibration_id`) REFERENCES `proc_DetectorIntercalibrationTable` (`id`),
  CONSTRAINT `proc_detectorintercalibrationsettable_ibfk_2` FOREIGN KEY (`ic_analysis_id`) REFERENCES `meas_AnalysisTable` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;



# Dump of table proc_DetectorIntercalibrationTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `proc_DetectorIntercalibrationTable`;

CREATE TABLE `proc_DetectorIntercalibrationTable` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `history_id` int(11) DEFAULT NULL,
  `detector_id` int(11) DEFAULT NULL,
  `user_value` double DEFAULT NULL,
  `user_error` double DEFAULT NULL,
  `fit` varchar(40) DEFAULT NULL,
  `set_id` int(11) DEFAULT NULL,
  `error_type` varchar(40) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `history_id` (`history_id`),
  KEY `detector_id` (`detector_id`),
  CONSTRAINT `proc_detectorintercalibrationtable_ibfk_1` FOREIGN KEY (`history_id`) REFERENCES `proc_DetectorIntercalibrationHistoryTable` (`id`),
  CONSTRAINT `proc_detectorintercalibrationtable_ibfk_2` FOREIGN KEY (`detector_id`) REFERENCES `gen_DetectorTable` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;



# Dump of table proc_DetectorParamHistoryTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `proc_DetectorParamHistoryTable`;

CREATE TABLE `proc_DetectorParamHistoryTable` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `create_date` datetime DEFAULT NULL,
  `user` varchar(40) DEFAULT NULL,
  `analysis_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `analysis_id` (`analysis_id`),
  CONSTRAINT `proc_detectorparamhistorytable_ibfk_1` FOREIGN KEY (`analysis_id`) REFERENCES `meas_AnalysisTable` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;



# Dump of table proc_DetectorParamTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `proc_DetectorParamTable`;

CREATE TABLE `proc_DetectorParamTable` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `history_id` int(11) DEFAULT NULL,
  `disc` float DEFAULT NULL,
  `disc_error` float DEFAULT NULL,
  `detector_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `history_id` (`history_id`),
  KEY `detector_id` (`detector_id`),
  CONSTRAINT `proc_detectorparamtable_ibfk_1` FOREIGN KEY (`history_id`) REFERENCES `proc_DetectorParamHistoryTable` (`id`),
  CONSTRAINT `proc_detectorparamtable_ibfk_2` FOREIGN KEY (`detector_id`) REFERENCES `gen_DetectorTable` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;



# Dump of table proc_FigureAnalysisTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `proc_FigureAnalysisTable`;

CREATE TABLE `proc_FigureAnalysisTable` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `figure_id` int(11) DEFAULT NULL,
  `analysis_id` int(11) DEFAULT NULL,
  `status` int(11) DEFAULT NULL,
  `graph` int(11) DEFAULT NULL,
  `group` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `figure_id` (`figure_id`),
  KEY `analysis_id` (`analysis_id`),
  CONSTRAINT `proc_figureanalysistable_ibfk_1` FOREIGN KEY (`figure_id`) REFERENCES `proc_FigureTable` (`id`),
  CONSTRAINT `proc_figureanalysistable_ibfk_2` FOREIGN KEY (`analysis_id`) REFERENCES `meas_AnalysisTable` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;



# Dump of table proc_FigureLabTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `proc_FigureLabTable`;

CREATE TABLE `proc_FigureLabTable` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `sample_id` int(11) DEFAULT NULL,
  `figure_id` int(11) DEFAULT NULL,
  `lab_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `lab_id` (`lab_id`),
  CONSTRAINT `proc_figurelabtable_ibfk_1` FOREIGN KEY (`lab_id`) REFERENCES `gen_LabTable` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;



# Dump of table proc_FigurePrefTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `proc_FigurePrefTable`;

CREATE TABLE `proc_FigurePrefTable` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `figure_id` int(11) DEFAULT NULL,
  `xbounds` varchar(80) DEFAULT NULL,
  `ybounds` varchar(80) DEFAULT NULL,
  `options` blob,
  `kind` varchar(40) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `figure_id` (`figure_id`),
  CONSTRAINT `proc_figurepreftable_ibfk_1` FOREIGN KEY (`figure_id`) REFERENCES `proc_FigureTable` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;



# Dump of table proc_FigureTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `proc_FigureTable`;

CREATE TABLE `proc_FigureTable` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(80) DEFAULT NULL,
  `create_date` datetime DEFAULT NULL,
  `user` varchar(40) DEFAULT NULL,
  `project_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `project_id` (`project_id`),
  CONSTRAINT `proc_figuretable_ibfk_1` FOREIGN KEY (`project_id`) REFERENCES `gen_ProjectTable` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;



# Dump of table proc_FitHistoryTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `proc_FitHistoryTable`;

CREATE TABLE `proc_FitHistoryTable` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `create_date` datetime DEFAULT NULL,
  `user` varchar(40) DEFAULT NULL,
  `analysis_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `analysis_id` (`analysis_id`),
  CONSTRAINT `proc_fithistorytable_ibfk_1` FOREIGN KEY (`analysis_id`) REFERENCES `meas_AnalysisTable` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;



# Dump of table proc_FitTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `proc_FitTable`;

CREATE TABLE `proc_FitTable` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `history_id` int(11) DEFAULT NULL,
  `isotope_id` int(11) DEFAULT NULL,
  `fit` varchar(40) DEFAULT NULL,
  `filter_outliers` tinyint(1) DEFAULT NULL,
  `filter_outlier_iterations` int(11) DEFAULT NULL,
  `filter_outlier_std_devs` int(11) DEFAULT NULL,
  `error_type` varchar(40) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `history_id` (`history_id`),
  KEY `isotope_id` (`isotope_id`),
  CONSTRAINT `proc_fittable_ibfk_1` FOREIGN KEY (`history_id`) REFERENCES `proc_FitHistoryTable` (`id`),
  CONSTRAINT `proc_fittable_ibfk_2` FOREIGN KEY (`isotope_id`) REFERENCES `meas_IsotopeTable` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;



# Dump of table proc_InterpretedAgeGroupHistoryTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `proc_InterpretedAgeGroupHistoryTable`;

CREATE TABLE `proc_InterpretedAgeGroupHistoryTable` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(80) DEFAULT NULL,
  `project_id` int(11) DEFAULT NULL,
  `create_date` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;



# Dump of table proc_InterpretedAgeGroupSetTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `proc_InterpretedAgeGroupSetTable`;

CREATE TABLE `proc_InterpretedAgeGroupSetTable` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `group_id` int(11) DEFAULT NULL,
  `interpreted_age_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;



# Dump of table proc_InterpretedAgeHistoryTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `proc_InterpretedAgeHistoryTable`;

CREATE TABLE `proc_InterpretedAgeHistoryTable` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `create_date` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `user` varchar(80) DEFAULT NULL,
  `identifier` varchar(80) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;



# Dump of table proc_InterpretedAgeSetTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `proc_InterpretedAgeSetTable`;

CREATE TABLE `proc_InterpretedAgeSetTable` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `analysis_id` int(11) DEFAULT NULL,
  `interpreted_age_id` int(11) DEFAULT NULL,
  `forced_plateau_step` tinyint(1) DEFAULT NULL,
  `plateau_step` tinyint(1) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `analysis_id` (`analysis_id`),
  KEY `interpreted_age_id` (`interpreted_age_id`),
  CONSTRAINT `proc_interpretedagesettable_ibfk_1` FOREIGN KEY (`analysis_id`) REFERENCES `meas_AnalysisTable` (`id`),
  CONSTRAINT `proc_interpretedagesettable_ibfk_2` FOREIGN KEY (`interpreted_age_id`) REFERENCES `proc_InterpretedAgeTable` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;



# Dump of table proc_InterpretedAgeTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `proc_InterpretedAgeTable`;

CREATE TABLE `proc_InterpretedAgeTable` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `history_id` int(11) DEFAULT NULL,
  `age_kind` varchar(32) DEFAULT NULL,
  `age` float DEFAULT NULL,
  `age_err` float DEFAULT NULL,
  `mswd` float DEFAULT NULL,
  `wtd_kca` float DEFAULT NULL,
  `wtd_kca_err` float DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `history_id` (`history_id`),
  CONSTRAINT `proc_interpretedagetable_ibfk_1` FOREIGN KEY (`history_id`) REFERENCES `proc_InterpretedAgeHistoryTable` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;



# Dump of table proc_IsotopeResultsTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `proc_IsotopeResultsTable`;

CREATE TABLE `proc_IsotopeResultsTable` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `signal_` double DEFAULT NULL,
  `signal_err` double DEFAULT NULL,
  `isotope_id` int(11) DEFAULT NULL,
  `history_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `isotope_id` (`isotope_id`),
  KEY `history_id` (`history_id`),
  CONSTRAINT `proc_isotoperesultstable_ibfk_1` FOREIGN KEY (`isotope_id`) REFERENCES `meas_IsotopeTable` (`id`),
  CONSTRAINT `proc_isotoperesultstable_ibfk_2` FOREIGN KEY (`history_id`) REFERENCES `proc_FitHistoryTable` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;



# Dump of table proc_NotesTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `proc_NotesTable`;

CREATE TABLE `proc_NotesTable` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `create_date` datetime DEFAULT NULL,
  `user` varchar(40) DEFAULT NULL,
  `note` blob,
  `analysis_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `analysis_id` (`analysis_id`),
  CONSTRAINT `proc_notestable_ibfk_1` FOREIGN KEY (`analysis_id`) REFERENCES `meas_AnalysisTable` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;



# Dump of table proc_SelectedHistoriesTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `proc_SelectedHistoriesTable`;

CREATE TABLE `proc_SelectedHistoriesTable` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `analysis_id` int(11) DEFAULT NULL,
  `selected_blanks_id` int(11) DEFAULT NULL,
  `selected_backgrounds_id` int(11) DEFAULT NULL,
  `selected_det_intercal_id` int(11) DEFAULT NULL,
  `selected_fits_id` int(11) DEFAULT NULL,
  `selected_arar_id` int(11) DEFAULT NULL,
  `selected_det_param_id` int(11) DEFAULT NULL,
  `selected_sensitivity_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `analysis_id` (`analysis_id`),
  KEY `selected_blanks_id` (`selected_blanks_id`),
  KEY `selected_backgrounds_id` (`selected_backgrounds_id`),
  KEY `selected_det_intercal_id` (`selected_det_intercal_id`),
  KEY `selected_fits_id` (`selected_fits_id`),
  KEY `selected_arar_id` (`selected_arar_id`),
  KEY `selected_det_param_id` (`selected_det_param_id`),
  KEY `selected_sensitivity_id` (`selected_sensitivity_id`),
  CONSTRAINT `proc_selectedhistoriestable_ibfk_1` FOREIGN KEY (`analysis_id`) REFERENCES `meas_AnalysisTable` (`id`),
  CONSTRAINT `proc_selectedhistoriestable_ibfk_2` FOREIGN KEY (`selected_blanks_id`) REFERENCES `proc_BlanksHistoryTable` (`id`),
  CONSTRAINT `proc_selectedhistoriestable_ibfk_3` FOREIGN KEY (`selected_backgrounds_id`) REFERENCES `proc_BackgroundsHistoryTable` (`id`),
  CONSTRAINT `proc_selectedhistoriestable_ibfk_4` FOREIGN KEY (`selected_det_intercal_id`) REFERENCES `proc_DetectorIntercalibrationHistoryTable` (`id`),
  CONSTRAINT `proc_selectedhistoriestable_ibfk_5` FOREIGN KEY (`selected_fits_id`) REFERENCES `proc_FitHistoryTable` (`id`),
  CONSTRAINT `proc_selectedhistoriestable_ibfk_6` FOREIGN KEY (`selected_arar_id`) REFERENCES `proc_ArArHistoryTable` (`id`),
  CONSTRAINT `proc_selectedhistoriestable_ibfk_7` FOREIGN KEY (`selected_det_param_id`) REFERENCES `proc_DetectorParamHistoryTable` (`id`),
  CONSTRAINT `proc_selectedhistoriestable_ibfk_8` FOREIGN KEY (`selected_sensitivity_id`) REFERENCES `proc_SensitivityHistoryTable` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;



# Dump of table proc_SensitivityHistoryTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `proc_SensitivityHistoryTable`;

CREATE TABLE `proc_SensitivityHistoryTable` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `create_date` datetime DEFAULT NULL,
  `analysis_id` int(11) DEFAULT NULL,
  `user` varchar(40) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `analysis_id` (`analysis_id`),
  CONSTRAINT `proc_sensitivityhistorytable_ibfk_1` FOREIGN KEY (`analysis_id`) REFERENCES `meas_AnalysisTable` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;



# Dump of table proc_SensitivityTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `proc_SensitivityTable`;

CREATE TABLE `proc_SensitivityTable` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `value` double DEFAULT NULL,
  `error` double DEFAULT NULL,
  `history_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `history_id` (`history_id`),
  CONSTRAINT `proc_sensitivitytable_ibfk_1` FOREIGN KEY (`history_id`) REFERENCES `proc_SensitivityHistoryTable` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;



# Dump of table proc_TagTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `proc_TagTable`;

CREATE TABLE `proc_TagTable` (
  `name` varchar(40) NOT NULL,
  `create_date` datetime DEFAULT NULL,
  `user` varchar(40) DEFAULT NULL,
  `omit_ideo` tinyint(1) DEFAULT NULL,
  `omit_spec` tinyint(1) DEFAULT NULL,
  `omit_iso` tinyint(1) DEFAULT NULL,
  `omit_series` tinyint(1) DEFAULT NULL,
  PRIMARY KEY (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;



# Dump of table proc_WorkspaceSettings
# ------------------------------------------------------------

DROP TABLE IF EXISTS `proc_WorkspaceSettings`;

CREATE TABLE `proc_WorkspaceSettings` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;



# Dump of table spec_MassCalHistoryTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `spec_MassCalHistoryTable`;

CREATE TABLE `spec_MassCalHistoryTable` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `create_date` datetime DEFAULT NULL,
  `spectrometer_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;



# Dump of table spec_MassCalScanTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `spec_MassCalScanTable`;

CREATE TABLE `spec_MassCalScanTable` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `history_id` int(11) DEFAULT NULL,
  `blob` blob,
  `center` float DEFAULT NULL,
  `molecular_weight_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `history_id` (`history_id`),
  KEY `molecular_weight_id` (`molecular_weight_id`),
  CONSTRAINT `spec_masscalscantable_ibfk_1` FOREIGN KEY (`history_id`) REFERENCES `spec_MassCalHistoryTable` (`id`),
  CONSTRAINT `spec_masscalscantable_ibfk_2` FOREIGN KEY (`molecular_weight_id`) REFERENCES `gen_MolecularWeightTable` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;




/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;
/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
