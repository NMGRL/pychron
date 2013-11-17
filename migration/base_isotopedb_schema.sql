# ************************************************************
# Sequel Pro SQL dump
# Version 4096
#
# http://www.sequelpro.com/
# http://code.google.com/p/sequel-pro/
#
# Host: 127.0.0.1 (MySQL 5.5.20-log)
# Database: isotopedb_dev_migrate
# Generation Time: 2013-11-17 20:50:12 +0000
# ************************************************************


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;


# Dump of table flux_FluxTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `flux_FluxTable`;

CREATE TABLE `flux_FluxTable` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `j` float DEFAULT NULL,
  `j_err` float DEFAULT NULL,
  `history_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY ```flux_FluxTable_history_id_fkey``` (`history_id`),
  CONSTRAINT ```flux_FluxTable_history_id_fkey``` FOREIGN KEY (`history_id`) REFERENCES `flux_HistoryTable` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;



# Dump of table flux_HistoryTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `flux_HistoryTable`;

CREATE TABLE `flux_HistoryTable` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `note` blob,
  `flux_monitor_id` int(11) DEFAULT NULL,
  `irradiation_position_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY ```flux_HistoryTable_flux_monitor_id_fkey``` (`flux_monitor_id`),
  KEY ```flux_HistoryTable_irradiation_position_id_fkey``` (`irradiation_position_id`),
  CONSTRAINT ```flux_HistoryTable_flux_monitor_id_fkey``` FOREIGN KEY (`flux_monitor_id`) REFERENCES `flux_MonitorTable` (`id`),
  CONSTRAINT ```flux_HistoryTable_irradiation_position_id_fkey``` FOREIGN KEY (`irradiation_position_id`) REFERENCES `irrad_PositionTable` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;



# Dump of table flux_MonitorTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `flux_MonitorTable`;

CREATE TABLE `flux_MonitorTable` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `decay_constant` float DEFAULT NULL,
  `age` float DEFAULT NULL,
  `age_err` float DEFAULT NULL,
  `sample_id` int(11) DEFAULT NULL,
  `name` varchar(80) DEFAULT NULL,
  `decay_constant_err` float DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY ```flux_MonitorTable_sample_id_fkey``` (`sample_id`),
  CONSTRAINT ```flux_MonitorTable_sample_id_fkey``` FOREIGN KEY (`sample_id`) REFERENCES `gen_SampleTable` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;



# Dump of table gen_AnalysisTypeTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `gen_AnalysisTypeTable`;

CREATE TABLE `gen_AnalysisTypeTable` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(40) NOT NULL,
  PRIMARY KEY (`id`,`name`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;



# Dump of table gen_DetectorTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `gen_DetectorTable`;

CREATE TABLE `gen_DetectorTable` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(40) DEFAULT NULL,
  `kind` varchar(40) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;



# Dump of table gen_ExtractionDeviceTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `gen_ExtractionDeviceTable`;

CREATE TABLE `gen_ExtractionDeviceTable` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(80) DEFAULT NULL,
  `kind` varchar(80) DEFAULT NULL,
  `make` varchar(80) DEFAULT NULL,
  `model` varchar(80) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;



# Dump of table gen_ImportTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `gen_ImportTable`;

CREATE TABLE `gen_ImportTable` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `date` datetime DEFAULT NULL,
  `user` varchar(80) DEFAULT NULL,
  `source_host` varchar(200) DEFAULT NULL,
  `source` varchar(200) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;



# Dump of table gen_LabTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `gen_LabTable`;

CREATE TABLE `gen_LabTable` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `irradiation_id` int(11) DEFAULT NULL,
  `sample_id` int(11) DEFAULT NULL,
  `selected_flux_id` int(11) DEFAULT NULL,
  `note` varchar(140) DEFAULT NULL,
  `identifier` varchar(45) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY ```gen_LabTable_irradiation_id_fkey``` (`irradiation_id`),
  KEY ```gen_LabTable_selected_flux_id_fkey``` (`selected_flux_id`),
  CONSTRAINT ```gen_LabTable_irradiation_id_fkey``` FOREIGN KEY (`irradiation_id`) REFERENCES `irrad_PositionTable` (`id`),
  CONSTRAINT ```gen_LabTable_selected_flux_id_fkey``` FOREIGN KEY (`selected_flux_id`) REFERENCES `flux_HistoryTable` (`id`)
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
  `name` varchar(40) DEFAULT NULL,
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
  `name` varchar(40) DEFAULT NULL,
  `mass` float DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;



# Dump of table gen_ProjectTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `gen_ProjectTable`;

CREATE TABLE `gen_ProjectTable` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(40) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

LOCK TABLES `gen_ProjectTable` WRITE;
/*!40000 ALTER TABLE `gen_ProjectTable` DISABLE KEYS */;

INSERT INTO `gen_ProjectTable` (`id`, `name`)
VALUES
	(1,'hgh'),
	(2,'jkj'),
	(3,'jiii');

/*!40000 ALTER TABLE `gen_ProjectTable` ENABLE KEYS */;
UNLOCK TABLES;


# Dump of table gen_SampleTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `gen_SampleTable`;

CREATE TABLE `gen_SampleTable` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(80) DEFAULT NULL,
  `project_id` int(11) DEFAULT NULL,
  `material_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY ```gen_SampleTable_project_id_fkey``` (`project_id`),
  KEY ```gen_SampleTable_material_id_fkey``` (`material_id`),
  CONSTRAINT ```gen_SampleTable_material_id_fkey``` FOREIGN KEY (`material_id`) REFERENCES `gen_MaterialTable` (`id`),
  CONSTRAINT ```gen_SampleTable_project_id_fkey``` FOREIGN KEY (`project_id`) REFERENCES `gen_ProjectTable` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;



# Dump of table gen_SensitivityTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `gen_SensitivityTable`;

CREATE TABLE `gen_SensitivityTable` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `sensitivity` double DEFAULT NULL,
  `mass_spectrometer_id` int(11) DEFAULT NULL,
  `user` varchar(40) DEFAULT NULL,
  `note` blob,
  `create_date` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY ```gen_SensitivityTable_mass_spectrometer_id_fkey``` (`mass_spectrometer_id`),
  CONSTRAINT ```gen_SensitivityTable_mass_spectrometer_id_fkey``` FOREIGN KEY (`mass_spectrometer_id`) REFERENCES `gen_MassSpectrometerTable` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;



# Dump of table gen_Usertable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `gen_Usertable`;

CREATE TABLE `gen_Usertable` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(40) DEFAULT NULL,
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
  `name` varchar(40) DEFAULT NULL,
  `geometry` blob,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;



# Dump of table irrad_IrradiationTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `irrad_IrradiationTable`;

CREATE TABLE `irrad_IrradiationTable` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `irradiation_production_id` int(11) DEFAULT NULL,
  `irradiation_chronology_id` int(11) DEFAULT NULL,
  `name` varchar(40) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY ```irrad_IrradiationTable_irradiation_production_id_fkey``` (`irradiation_production_id`),
  KEY ```irrad_IrradiationTable_irradiation_chronology_id_fkey``` (`irradiation_chronology_id`),
  CONSTRAINT ```irrad_IrradiationTable_irradiation_chronology_id_fkey``` FOREIGN KEY (`irradiation_chronology_id`) REFERENCES `irrad_ChronologyTable` (`id`),
  CONSTRAINT ```irrad_IrradiationTable_irradiation_production_id_fkey``` FOREIGN KEY (`irradiation_production_id`) REFERENCES `irrad_ProductionTable` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;



# Dump of table irrad_LevelTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `irrad_LevelTable`;

CREATE TABLE `irrad_LevelTable` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(40) DEFAULT NULL,
  `holder_id` int(11) DEFAULT NULL,
  `irradiation_id` int(11) DEFAULT NULL,
  `z` float DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY ```irrad_LevelTable_holder_id_fkey``` (`holder_id`),
  KEY ```irrad_LevelTable_irradiation_id_fkey``` (`irradiation_id`),
  CONSTRAINT ```irrad_LevelTable_holder_id_fkey``` FOREIGN KEY (`holder_id`) REFERENCES `irrad_HolderTable` (`id`),
  CONSTRAINT ```irrad_LevelTable_irradiation_id_fkey``` FOREIGN KEY (`irradiation_id`) REFERENCES `irrad_IrradiationTable` (`id`)
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
  KEY ```irrad_PositionTable_level_id_fkey``` (`level_id`),
  CONSTRAINT ```irrad_PositionTable_level_id_fkey``` FOREIGN KEY (`level_id`) REFERENCES `irrad_LevelTable` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;



# Dump of table irrad_ProductionTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `irrad_ProductionTable`;

CREATE TABLE `irrad_ProductionTable` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `Ca3637` float DEFAULT NULL,
  `Ca3637_err` float DEFAULT NULL,
  `Ca3837` float DEFAULT NULL,
  `Ca3837_err` float DEFAULT NULL,
  `Ca3937` float DEFAULT NULL,
  `Ca3937_err` float DEFAULT NULL,
  `K3739` float DEFAULT NULL,
  `K3739_err` float DEFAULT NULL,
  `K3839` float DEFAULT NULL,
  `K3839_err` float DEFAULT NULL,
  `K4039` float DEFAULT NULL,
  `K4039_err` float DEFAULT NULL,
  `Cl3638` float DEFAULT NULL,
  `Cl3638_err` float DEFAULT NULL,
  `name` varchar(40) DEFAULT NULL,
  `Ca_K` double DEFAULT NULL,
  `Ca_K_err` double DEFAULT NULL,
  `Cl_K` double DEFAULT NULL,
  `Cl_K_err` double DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;



# Dump of table loading_LoadTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `loading_LoadTable`;

CREATE TABLE `loading_LoadTable` (
  `name` varchar(80) NOT NULL,
  `create_date` datetime DEFAULT NULL,
  `holder` varchar(80) DEFAULT NULL,
  PRIMARY KEY (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;



# Dump of table loading_PositionsTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `loading_PositionsTable`;

CREATE TABLE `loading_PositionsTable` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `position` int(11) DEFAULT NULL,
  `lab_identifier` varchar(80) DEFAULT NULL,
  `load_identifier` varchar(80) DEFAULT NULL,
  `weight` float DEFAULT NULL,
  PRIMARY KEY (`id`)
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
  `endtime` time DEFAULT NULL,
  `status` int(11) DEFAULT NULL,
  `aliquot` int(11) DEFAULT NULL,
  `step` varchar(10) DEFAULT NULL,
  `import_id` int(11) DEFAULT NULL,
  `uuid` varchar(36) DEFAULT NULL,
  `analysis_timestamp` datetime DEFAULT NULL,
  `comment` blob,
  `user_id` int(11) DEFAULT NULL,
  `tag` varchar(40) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY ```meas_AnalysisTable_extraction_id_fkey``` (`extraction_id`),
  KEY ```meas_AnalysisTable_measurement_id_fkey``` (`measurement_id`),
  KEY ```meas_AnalysisTable_experiment_id_fkey``` (`experiment_id`),
  KEY ```meas_AnalysisTable_lab_id_fkey``` (`lab_id`),
  KEY ```meas_AnalysisTable_import_id_fkey``` (`import_id`),
  KEY ```meas_AnalysisTable_user_id_fkey``` (`user_id`),
  CONSTRAINT ```meas_AnalysisTable_experiment_id_fkey``` FOREIGN KEY (`experiment_id`) REFERENCES `meas_ExperimentTable` (`id`),
  CONSTRAINT ```meas_AnalysisTable_extraction_id_fkey``` FOREIGN KEY (`extraction_id`) REFERENCES `meas_ExtractionTable` (`id`),
  CONSTRAINT ```meas_AnalysisTable_import_id_fkey``` FOREIGN KEY (`import_id`) REFERENCES `gen_ImportTable` (`id`),
  CONSTRAINT ```meas_AnalysisTable_lab_id_fkey``` FOREIGN KEY (`lab_id`) REFERENCES `gen_LabTable` (`id`),
  CONSTRAINT ```meas_AnalysisTable_measurement_id_fkey``` FOREIGN KEY (`measurement_id`) REFERENCES `meas_MeasurementTable` (`id`),
  CONSTRAINT ```meas_AnalysisTable_user_id_fkey``` FOREIGN KEY (`user_id`) REFERENCES `gen_UserTable` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;



# Dump of table meas_ExperimentTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `meas_ExperimentTable`;

CREATE TABLE `meas_ExperimentTable` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(40) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;



# Dump of table meas_ExtractionTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `meas_ExtractionTable`;

CREATE TABLE `meas_ExtractionTable` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `extract_device_id` int(11) DEFAULT NULL,
  `extract_value` float DEFAULT NULL,
  `extract_duration` float DEFAULT NULL,
  `cleanup_duration` float DEFAULT NULL,
  `weight` float DEFAULT NULL,
  `sensitivity_multiplier` float DEFAULT NULL,
  `sensitivity_id` int(11) DEFAULT NULL,
  `script_id` int(11) DEFAULT NULL,
  `experiment_blob_id` int(11) DEFAULT NULL,
  `image_id` int(11) DEFAULT NULL,
  `is_degas` tinyint(1) DEFAULT NULL,
  `extract_units` varchar(5) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `extract_device_id` (`extract_device_id`),
  KEY ```meas_ExtractionTable_sensitivity_id_fkey``` (`sensitivity_id`),
  KEY ```meas_ExtractionTable_script_id_fkey``` (`script_id`),
  KEY ```meas_ExtractionTable_experiment_blob_id_fkey``` (`experiment_blob_id`),
  KEY ```meas_ExtractionTable_image_id_fkey``` (`image_id`),
  CONSTRAINT `meas_extractiontable_ibfk_1` FOREIGN KEY (`extract_device_id`) REFERENCES `gen_ExtractionDeviceTable` (`id`),
  CONSTRAINT ```meas_ExtractionTable_experiment_blob_id_fkey``` FOREIGN KEY (`experiment_blob_id`) REFERENCES `meas_ScriptTable` (`id`),
  CONSTRAINT ```meas_ExtractionTable_image_id_fkey``` FOREIGN KEY (`image_id`) REFERENCES `med_ImageTable` (`id`),
  CONSTRAINT ```meas_ExtractionTable_script_id_fkey``` FOREIGN KEY (`script_id`) REFERENCES `meas_ScriptTable` (`id`),
  CONSTRAINT ```meas_ExtractionTable_sensitivity_id_fkey``` FOREIGN KEY (`sensitivity_id`) REFERENCES `gen_SensitivityTable` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

LOCK TABLES `meas_ExtractionTable` WRITE;
/*!40000 ALTER TABLE `meas_ExtractionTable` DISABLE KEYS */;

INSERT INTO `meas_ExtractionTable` (`id`, `extract_device_id`, `extract_value`, `extract_duration`, `cleanup_duration`, `weight`, `sensitivity_multiplier`, `sensitivity_id`, `script_id`, `experiment_blob_id`, `image_id`, `is_degas`, `extract_units`)
VALUES
	(1,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
	(2,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL);

/*!40000 ALTER TABLE `meas_ExtractionTable` ENABLE KEYS */;
UNLOCK TABLES;


# Dump of table meas_IsotopeTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `meas_IsotopeTable`;

CREATE TABLE `meas_IsotopeTable` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `analysis_id` int(11) DEFAULT NULL,
  `detector_id` int(11) DEFAULT NULL,
  `molecular_weight_id` int(11) DEFAULT NULL,
  `kind` varchar(40) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY ```meas_IsotopeTable_molecular_weight_id_fkey``` (`molecular_weight_id`),
  CONSTRAINT ```meas_IsotopeTable_molecular_weight_id_fkey``` FOREIGN KEY (`molecular_weight_id`) REFERENCES `gen_MolecularWeightTable` (`id`)
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
  KEY ```meas_MeasurementTable_mass_spectrometer_id_fkey``` (`mass_spectrometer_id`),
  KEY ```meas_MeasurementTable_analysis_type_id_fkey``` (`analysis_type_id`),
  KEY ```meas_MeasurementTable_spectrometer_parameters_id_fkey``` (`spectrometer_parameters_id`),
  KEY ```meas_MeasurementTable_script_id_fkey``` (`script_id`),
  CONSTRAINT ```meas_MeasurementTable_analysis_type_id_fkey``` FOREIGN KEY (`analysis_type_id`) REFERENCES `gen_AnalysisTypeTable` (`id`),
  CONSTRAINT ```meas_MeasurementTable_mass_spectrometer_id_fkey``` FOREIGN KEY (`mass_spectrometer_id`) REFERENCES `gen_MassSpectrometerTable` (`id`),
  CONSTRAINT ```meas_MeasurementTable_script_id_fkey``` FOREIGN KEY (`script_id`) REFERENCES `meas_ScriptTable` (`id`),
  CONSTRAINT ```meas_MeasurementTable_spectrometer_parameters_id_fkey``` FOREIGN KEY (`spectrometer_parameters_id`) REFERENCES `meas_SpectrometerParametersTable` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;



# Dump of table meas_MonitorTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `meas_MonitorTable`;

CREATE TABLE `meas_MonitorTable` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `analysis_id` int(11) DEFAULT NULL,
  `xydata` blob,
  `name` varchar(80) DEFAULT NULL,
  `parameter` varchar(40) DEFAULT NULL,
  `criterion` varchar(40) DEFAULT NULL,
  `comparator` varchar(40) DEFAULT NULL,
  `action` varchar(40) DEFAULT NULL,
  `tripped` tinyint(1) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY ```meas_MonitorTable_analysis_id_fkey``` (`analysis_id`),
  CONSTRAINT ```meas_MonitorTable_analysis_id_fkey``` FOREIGN KEY (`analysis_id`) REFERENCES `meas_AnalysisTable` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;



# Dump of table meas_PeakCenterTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `meas_PeakCenterTable`;

CREATE TABLE `meas_PeakCenterTable` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `analysis_id` int(11) DEFAULT NULL,
  `center` double DEFAULT NULL,
  `points` blob,
  PRIMARY KEY (`id`),
  KEY ```meas_PeakCenterTable_analysis_id_fkey``` (`analysis_id`),
  CONSTRAINT ```meas_PeakCenterTable_analysis_id_fkey``` FOREIGN KEY (`analysis_id`) REFERENCES `meas_AnalysisTable` (`id`)
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
  `extraction_id` int(11) DEFAULT NULL,
  `is_degas` tinyint(1) DEFAULT NULL,
  `load_identifier` varchar(80) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY ```meas_PositionTable_extraction_id_fkey``` (`extraction_id`),
  CONSTRAINT ```meas_PositionTable_extraction_id_fkey``` FOREIGN KEY (`extraction_id`) REFERENCES `meas_ExtractionTable` (`id`)
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
  KEY ```meas_SignalTable_isotope_id_fkey``` (`isotope_id`),
  CONSTRAINT ```meas_SignalTable_isotope_id_fkey``` FOREIGN KEY (`isotope_id`) REFERENCES `meas_IsotopeTable` (`id`)
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
  KEY ```meas_SpectrometerDeflectionsTable_detector_id_fkey``` (`detector_id`),
  KEY ```meas_SpectrometerDeflectionsTable_measurement_id_fkey``` (`measurement_id`),
  CONSTRAINT ```meas_SpectrometerDeflectionsTable_detector_id_fkey``` FOREIGN KEY (`detector_id`) REFERENCES `gen_DetectorTable` (`id`),
  CONSTRAINT ```meas_SpectrometerDeflectionsTable_measurement_id_fkey``` FOREIGN KEY (`measurement_id`) REFERENCES `meas_MeasurementTable` (`id`)
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
  `create_date` datetime DEFAULT NULL,
  `extraction_id` int(11) DEFAULT NULL,
  `path` varchar(200) DEFAULT NULL,
  `image` blob,
  PRIMARY KEY (`id`),
  KEY ```med_SnapshotTable_extraction_id_fkey``` (`extraction_id`),
  CONSTRAINT ```med_SnapshotTable_extraction_id_fkey``` FOREIGN KEY (`extraction_id`) REFERENCES `meas_ExtractionTable` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;



# Dump of table migrate_version
# ------------------------------------------------------------

DROP TABLE IF EXISTS `migrate_version`;

CREATE TABLE `migrate_version` (
  `repository_id` varchar(250) NOT NULL,
  `repository_path` text,
  `version` int(11) DEFAULT NULL,
  PRIMARY KEY (`repository_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

LOCK TABLES `migrate_version` WRITE;
/*!40000 ALTER TABLE `migrate_version` DISABLE KEYS */;

INSERT INTO `migrate_version` (`repository_id`, `repository_path`, `version`)
VALUES
	('Isotope Database','isotopedb/',81);

/*!40000 ALTER TABLE `migrate_version` ENABLE KEYS */;
UNLOCK TABLES;


# Dump of table proc_ArArHistoryTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `proc_ArArHistoryTable`;

CREATE TABLE `proc_ArArHistoryTable` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `analysis_id` int(11) DEFAULT NULL,
  `create_date` datetime DEFAULT NULL,
  `user` varchar(40) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;



# Dump of table proc_ArArTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `proc_ArArTable`;

CREATE TABLE `proc_ArArTable` (
  `history_id` int(11) DEFAULT NULL,
  `age` float DEFAULT NULL,
  `age_err` float DEFAULT NULL,
  `id` int(11) NOT NULL DEFAULT '0',
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
  `k39` float DEFAULT NULL,
  `k39_err` float DEFAULT NULL,
  `ca37` float DEFAULT NULL,
  `ca37_err` float DEFAULT NULL,
  `cl36` float DEFAULT NULL,
  `cl36_err` float DEFAULT NULL,
  `rad40` float DEFAULT NULL,
  `rad40_err` float DEFAULT NULL,
  `age_err_wo_j` float DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;



# Dump of table proc_BackgroundsHistoryTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `proc_BackgroundsHistoryTable`;

CREATE TABLE `proc_BackgroundsHistoryTable` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `analysis_id` int(11) DEFAULT NULL,
  `create_date` datetime DEFAULT NULL,
  `user` varchar(40) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY ```proc_BackgroundsHistoryTable_analysis_id_fkey``` (`analysis_id`),
  CONSTRAINT ```proc_BackgroundsHistoryTable_analysis_id_fkey``` FOREIGN KEY (`analysis_id`) REFERENCES `meas_AnalysisTable` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;



# Dump of table proc_BackgroundsSetTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `proc_BackgroundsSetTable`;

CREATE TABLE `proc_BackgroundsSetTable` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `background_analysis_id` int(11) DEFAULT NULL,
  `backgrounds_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY ```proc_BackgroundsSetTable_background_analysis_id_fkey``` (`background_analysis_id`),
  KEY ```proc_BackgroundsSetTable_backgrounds_id_fkey``` (`backgrounds_id`),
  CONSTRAINT ```proc_BackgroundsSetTable_backgrounds_id_fkey``` FOREIGN KEY (`backgrounds_id`) REFERENCES `proc_BackgroundsTable` (`id`),
  CONSTRAINT ```proc_BackgroundsSetTable_background_analysis_id_fkey``` FOREIGN KEY (`background_analysis_id`) REFERENCES `meas_AnalysisTable` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;



# Dump of table proc_BackgroundsTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `proc_BackgroundsTable`;

CREATE TABLE `proc_BackgroundsTable` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `history_id` int(11) DEFAULT NULL,
  `user_value` double DEFAULT NULL,
  `user_error` double DEFAULT NULL,
  `use_set` tinyint(1) DEFAULT NULL,
  `isotope` varchar(40) DEFAULT NULL,
  `fit` varchar(40) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY ```proc_BackgroundsTable_history_id_fkey``` (`history_id`),
  CONSTRAINT ```proc_BackgroundsTable_history_id_fkey``` FOREIGN KEY (`history_id`) REFERENCES `proc_BackgroundsHistoryTable` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;



# Dump of table proc_BlanksHistoryTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `proc_BlanksHistoryTable`;

CREATE TABLE `proc_BlanksHistoryTable` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `analysis_id` int(11) DEFAULT NULL,
  `create_date` datetime DEFAULT NULL,
  `user` varchar(40) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY ```proc_BlanksHistoryTable_analysis_id_fkey``` (`analysis_id`),
  CONSTRAINT ```proc_BlanksHistoryTable_analysis_id_fkey``` FOREIGN KEY (`analysis_id`) REFERENCES `meas_AnalysisTable` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;



# Dump of table proc_BlanksSetTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `proc_BlanksSetTable`;

CREATE TABLE `proc_BlanksSetTable` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `blank_analysis_id` int(11) DEFAULT NULL,
  `blanks_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY ```proc_BlanksSetTable_blank_analysis_id_fkey``` (`blank_analysis_id`),
  KEY ```proc_BlanksSetTable_blanks_id_fkey``` (`blanks_id`),
  CONSTRAINT ```proc_BlanksSetTable_blanks_id_fkey``` FOREIGN KEY (`blanks_id`) REFERENCES `proc_BlanksTable` (`id`),
  CONSTRAINT ```proc_BlanksSetTable_blank_analysis_id_fkey``` FOREIGN KEY (`blank_analysis_id`) REFERENCES `meas_AnalysisTable` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;



# Dump of table proc_BlanksTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `proc_BlanksTable`;

CREATE TABLE `proc_BlanksTable` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `history_id` int(11) DEFAULT NULL,
  `user_value` double DEFAULT NULL,
  `user_error` double DEFAULT NULL,
  `use_set` tinyint(1) DEFAULT NULL,
  `isotope` varchar(40) DEFAULT NULL,
  `fit` varchar(40) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY ```proc_BlanksTable_history_id_fkey``` (`history_id`),
  CONSTRAINT ```proc_BlanksTable_history_id_fkey``` FOREIGN KEY (`history_id`) REFERENCES `proc_BlanksHistoryTable` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;



# Dump of table proc_DetectorIntercalibrationHistoryTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `proc_DetectorIntercalibrationHistoryTable`;

CREATE TABLE `proc_DetectorIntercalibrationHistoryTable` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `analysis_id` int(11) DEFAULT NULL,
  `create_date` datetime DEFAULT NULL,
  `user` varchar(40) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY ```proc_DetectorIntercalibrationHistoryTable_analysis_id_fkey``` (`analysis_id`),
  CONSTRAINT ```proc_DetectorIntercalibrationHistoryTable_analysis_id_fkey``` FOREIGN KEY (`analysis_id`) REFERENCES `meas_AnalysisTable` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;



# Dump of table proc_DetectorIntercalibrationSetTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `proc_DetectorIntercalibrationSetTable`;

CREATE TABLE `proc_DetectorIntercalibrationSetTable` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `ic_analysis_id` int(11) DEFAULT NULL,
  `intercalibration_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY ```proc_DetectorIntercalibrationSetTable_ic_analysis_id_fkey``` (`ic_analysis_id`),
  KEY ```proc_DetectorIntercalibrationSetTable_intercalibration_id_fkey``` (`intercalibration_id`),
  CONSTRAINT ```proc_DetectorIntercalibrationSetTable_ic_analysis_id_fkey``` FOREIGN KEY (`ic_analysis_id`) REFERENCES `meas_AnalysisTable` (`id`),
  CONSTRAINT ```proc_DetectorIntercalibrationSetTable_intercalibration_id_fkey``` FOREIGN KEY (`intercalibration_id`) REFERENCES `proc_DetectorIntercalibrationTable` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;



# Dump of table proc_DetectorIntercalibrationTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `proc_DetectorIntercalibrationTable`;

CREATE TABLE `proc_DetectorIntercalibrationTable` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `history_id` int(11) DEFAULT NULL,
  `user_value` double DEFAULT NULL,
  `user_error` double DEFAULT NULL,
  `fit` varchar(40) DEFAULT NULL,
  `detector_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY ```proc_DetectorIntercalibrationTable_history_id_fkey``` (`history_id`),
  KEY ```proc_DetectorIntercalibrationTable_detector_id_fkey``` (`detector_id`),
  CONSTRAINT ```proc_DetectorIntercalibrationTable_detector_id_fkey``` FOREIGN KEY (`detector_id`) REFERENCES `gen_DetectorTable` (`id`),
  CONSTRAINT ```proc_DetectorIntercalibrationTable_history_id_fkey``` FOREIGN KEY (`history_id`) REFERENCES `proc_DetectorIntercalibrationHistoryTable` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;



# Dump of table proc_DetectorParamHistoryTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `proc_DetectorParamHistoryTable`;

CREATE TABLE `proc_DetectorParamHistoryTable` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user` varchar(40) DEFAULT NULL,
  `create_date` datetime DEFAULT NULL,
  `analysis_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;



# Dump of table proc_DetectorParamTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `proc_DetectorParamTable`;

CREATE TABLE `proc_DetectorParamTable` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `detector_id` int(11) DEFAULT NULL,
  `history_id` int(11) DEFAULT NULL,
  `disc` float DEFAULT NULL,
  `disc_error` float DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;



# Dump of table proc_FigureAnalysisTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `proc_FigureAnalysisTable`;

CREATE TABLE `proc_FigureAnalysisTable` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `analysis_id` int(11) DEFAULT NULL,
  `figure_id` int(11) DEFAULT NULL,
  `status` int(11) DEFAULT NULL,
  `graph` int(11) DEFAULT NULL,
  `group` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY ```proc_FigureAnalysisTable_analysis_id_fkey``` (`analysis_id`),
  KEY ```proc_FigureAnalysisTable_figure_id_fkey``` (`figure_id`),
  CONSTRAINT ```proc_FigureAnalysisTable_analysis_id_fkey``` FOREIGN KEY (`analysis_id`) REFERENCES `meas_AnalysisTable` (`id`),
  CONSTRAINT ```proc_FigureAnalysisTable_figure_id_fkey``` FOREIGN KEY (`figure_id`) REFERENCES `meas_AnalysisTable` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;



# Dump of table proc_FigurePrefTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `proc_FigurePrefTable`;

CREATE TABLE `proc_FigurePrefTable` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `figure_id` int(11) DEFAULT NULL,
  `xbounds` varchar(80) DEFAULT NULL,
  `ybounds` varchar(80) DEFAULT NULL,
  `options_pickle` blob,
  PRIMARY KEY (`id`),
  KEY ```proc_FigurePrefTable_figure_id_fkey``` (`figure_id`),
  CONSTRAINT ```proc_FigurePrefTable_figure_id_fkey``` FOREIGN KEY (`figure_id`) REFERENCES `proc_FigureTable` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;



# Dump of table proc_FigureTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `proc_FigureTable`;

CREATE TABLE `proc_FigureTable` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(40) DEFAULT NULL,
  `project_id` int(11) DEFAULT NULL,
  `create_date` datetime DEFAULT NULL,
  `user` varchar(40) DEFAULT NULL,
  `note` blob,
  PRIMARY KEY (`id`),
  KEY ```proc_FigureTable_project_id_fkey``` (`project_id`),
  CONSTRAINT ```proc_FigureTable_project_id_fkey``` FOREIGN KEY (`project_id`) REFERENCES `gen_ProjectTable` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

LOCK TABLES `proc_FigureTable` WRITE;
/*!40000 ALTER TABLE `proc_FigureTable` DISABLE KEYS */;

INSERT INTO `proc_FigureTable` (`id`, `name`, `project_id`, `create_date`, `user`, `note`)
VALUES
	(1,NULL,2,NULL,NULL,NULL);

/*!40000 ALTER TABLE `proc_FigureTable` ENABLE KEYS */;
UNLOCK TABLES;


# Dump of table proc_FitHistoryTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `proc_FitHistoryTable`;

CREATE TABLE `proc_FitHistoryTable` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `analysis_id` int(11) DEFAULT NULL,
  `create_date` datetime DEFAULT NULL,
  `user` varchar(40) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY ```proc_FitHistoryTable_analysis_id_fkey``` (`analysis_id`),
  CONSTRAINT ```proc_FitHistoryTable_analysis_id_fkey``` FOREIGN KEY (`analysis_id`) REFERENCES `meas_AnalysisTable` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;



# Dump of table proc_FitTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `proc_FitTable`;

CREATE TABLE `proc_FitTable` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `history_id` int(11) DEFAULT NULL,
  `fit` varchar(40) DEFAULT NULL,
  `filter_outliers` tinyint(1) DEFAULT NULL,
  `filter_outlier_iterations` int(11) DEFAULT NULL,
  `filter_outlier_std_devs` int(11) DEFAULT NULL,
  `isotope_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY ```proc_FitTable_isotope_id_fkey``` (`isotope_id`),
  KEY ```proc_FitTable_history_id_fkey``` (`history_id`),
  CONSTRAINT ```proc_FitTable_history_id_fkey``` FOREIGN KEY (`history_id`) REFERENCES `proc_FitHistoryTable` (`id`),
  CONSTRAINT ```proc_FitTable_isotope_id_fkey``` FOREIGN KEY (`isotope_id`) REFERENCES `meas_IsotopeTable` (`id`)
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
  KEY ```proc_IsotopeResultsTable_history_id_fkey``` (`history_id`),
  KEY ```proc_IsotopeResultsTable_isotope_id_fkey``` (`isotope_id`),
  CONSTRAINT ```proc_IsotopeResultsTable_history_id_fkey``` FOREIGN KEY (`history_id`) REFERENCES `proc_FitHistoryTable` (`id`),
  CONSTRAINT ```proc_IsotopeResultsTable_isotope_id_fkey``` FOREIGN KEY (`isotope_id`) REFERENCES `meas_IsotopeTable` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;



# Dump of table proc_NotesTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `proc_NotesTable`;

CREATE TABLE `proc_NotesTable` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `note` blob,
  `analysis_id` int(11) DEFAULT NULL,
  `user` varchar(40) DEFAULT NULL,
  `create_date` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY ```proc_NotesTable_analysis_id_fkey``` (`analysis_id`),
  CONSTRAINT ```proc_NotesTable_analysis_id_fkey``` FOREIGN KEY (`analysis_id`) REFERENCES `meas_AnalysisTable` (`id`)
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
  PRIMARY KEY (`id`),
  KEY ```proc_SelectedHistoriesTable_analysis_id_fkey``` (`analysis_id`),
  KEY ```proc_SelectedHistoriesTable_selected_blanks_id_fkey``` (`selected_blanks_id`),
  KEY ```proc_SelectedHistoriesTable_selected_backgrounds_id_fkey``` (`selected_backgrounds_id`),
  KEY ```proc_SelectedHistoriesTable_selected_det_intercal_id_fkey``` (`selected_det_intercal_id`),
  KEY ```proc_SelectedHistoriesTable_selected_fits_id_fkey``` (`selected_fits_id`),
  KEY ```proc_SelectedHistoriesTable_selected_det_param_id_fkey``` (`selected_det_param_id`),
  KEY ```proc_SelectedHistoriesTable_selected_arar_id_fkey``` (`selected_arar_id`),
  CONSTRAINT ```proc_SelectedHistoriesTable_analysis_id_fkey``` FOREIGN KEY (`analysis_id`) REFERENCES `meas_AnalysisTable` (`id`),
  CONSTRAINT ```proc_SelectedHistoriesTable_selected_arar_id_fkey``` FOREIGN KEY (`selected_arar_id`) REFERENCES `proc_ArArHistoryTable` (`id`),
  CONSTRAINT ```proc_SelectedHistoriesTable_selected_backgrounds_id_fkey``` FOREIGN KEY (`selected_backgrounds_id`) REFERENCES `proc_BackgroundsHistoryTable` (`id`),
  CONSTRAINT ```proc_SelectedHistoriesTable_selected_blanks_id_fkey``` FOREIGN KEY (`selected_blanks_id`) REFERENCES `proc_BlanksHistoryTable` (`id`),
  CONSTRAINT ```proc_SelectedHistoriesTable_selected_det_intercal_id_fkey``` FOREIGN KEY (`selected_det_intercal_id`) REFERENCES `proc_DetectorIntercalibrationHistoryTable` (`id`),
  CONSTRAINT ```proc_SelectedHistoriesTable_selected_det_param_id_fkey``` FOREIGN KEY (`selected_det_param_id`) REFERENCES `proc_DetectorParamHistoryTable` (`id`),
  CONSTRAINT ```proc_SelectedHistoriesTable_selected_fits_id_fkey``` FOREIGN KEY (`selected_fits_id`) REFERENCES `proc_FitHistoryTable` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;



# Dump of table proc_TagTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `proc_TagTable`;

CREATE TABLE `proc_TagTable` (
  `name` varchar(40) NOT NULL,
  `user` varchar(40) DEFAULT NULL,
  `create_date` datetime DEFAULT NULL,
  `omit_ideo` tinyint(1) DEFAULT NULL,
  `omit_spec` tinyint(1) DEFAULT NULL,
  `omit_iso` tinyint(1) DEFAULT NULL,
  PRIMARY KEY (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;



# Dump of table spec_MassCalHistoryTable
# ------------------------------------------------------------

DROP TABLE IF EXISTS `spec_MassCalHistoryTable`;

CREATE TABLE `spec_MassCalHistoryTable` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `create_date` datetime DEFAULT NULL,
  `spectrometer_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY ```spec_MassCalHistoryTable_spectrometer_id_fkey``` (`spectrometer_id`),
  CONSTRAINT ```spec_MassCalHistoryTable_spectrometer_id_fkey``` FOREIGN KEY (`spectrometer_id`) REFERENCES `gen_MassSpectrometerTable` (`id`)
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
  KEY ```spec_MassCalScanTable_history_id_fkey``` (`history_id`),
  KEY ```spec_MassCalScanTable_molecular_weight_id_fkey``` (`molecular_weight_id`),
  CONSTRAINT ```spec_MassCalScanTable_history_id_fkey``` FOREIGN KEY (`history_id`) REFERENCES `spec_MassCalHistoryTable` (`id`),
  CONSTRAINT ```spec_MassCalScanTable_molecular_weight_id_fkey``` FOREIGN KEY (`molecular_weight_id`) REFERENCES `gen_MolecularWeightTable` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;




/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;
/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
