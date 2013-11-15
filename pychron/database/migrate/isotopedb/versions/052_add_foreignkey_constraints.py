from sqlalchemy import *
from migrate import *
from migrate.changeset.constraint import ForeignKeyConstraint

constraints = [
               ('flux_FluxTable', 'history', 'flux_HistoryTable'),
               ('flux_HistoryTable', 'flux_monitor', 'flux_MonitorTable'),
               ('flux_HistoryTable', 'irradiation_position', 'irrad_PositionTable'),
               ('flux_MonitorTable', 'sample', 'gen_SampleTable'),
               ('gen_LabTable', 'irradiation', 'irrad_PositionTable'),
               ('gen_LabTable', 'selected_flux', 'flux_HistoryTable'),
               ('gen_SampleTable', 'project', 'gen_ProjectTable'),
               ('gen_SampleTable', 'material', 'gen_MaterialTable'),
               ('irrad_IrradiationTable', 'irradiation_production', 'irrad_ProductionTable'),
               ('irrad_IrradiationTable', 'irradiation_chronology', 'irrad_ChronologyTable'),
               ('irrad_LevelTable', 'holder', 'irrad_HolderTable'),
               ('irrad_LevelTable', 'irradiation', 'irrad_IrradiationTable'),
               ('irrad_PositionTable', 'level', 'irrad_LevelTable'),
               ('meas_AnalysisTable', 'extraction', 'meas_ExtractionTable'),
               ('meas_AnalysisTable', 'measurement', 'meas_MeasurementTable'),
               ('meas_AnalysisTable', 'experiment', 'meas_ExperimentTable'),
               ('meas_AnalysisTable', 'lab', 'gen_LabTable'),
               ('meas_AnalysisTable', 'import', 'gen_ImportTable'),
               ('meas_IsotopeTable', 'molecular_weight', 'gen_MolecularWeightTable'),
               ('meas_MeasurementTable', 'mass_spectrometer', 'gen_MassSpectrometerTable'),
               ('meas_MeasurementTable', 'analysis_type', 'gen_AnalysisTypeTable'),
               ('meas_PeakCenterTable', 'analysis', 'meas_AnalysisTable'),
               ('meas_SignalTable', 'isotope', 'meas_IsotopeTable'),
               ('meas_SpectrometerDeflectionsTable', 'detector', 'gen_DetectorTable'),
               ('meas_SpectrometerDeflectionsTable', 'measurement', 'meas_MeasurementTable'),
               ('meas_SpectrometerParametersTable', 'measurement', 'meas_MeasurementTable'),
               ('proc_BackgroundsHistoryTable', 'analysis', 'meas_AnalysisTable'),
               ('proc_BackgroundsSetTable', 'background_analysis', 'meas_AnalysisTable'),
               ('proc_BackgroundsSetTable', 'backgrounds', 'proc_BackgroundsTable'),
               ('proc_BackgroundsTable', 'history', 'proc_BackgroundsHistoryTable'),
               ('proc_BlanksHistoryTable', 'analysis', 'meas_AnalysisTable'),
               ('proc_BlanksSetTable', 'blank_analysis', 'meas_AnalysisTable'),
               ('proc_BlanksSetTable', 'blanks', 'proc_BlanksTable'),
               ('proc_BlanksTable', 'history', 'proc_BlanksHistoryTable'),
               ('proc_DetectorIntercalibrationHistoryTable', 'analysis', 'meas_AnalysisTable'),
               ('proc_DetectorIntercalibrationSetTable', 'ic_analysis', 'meas_AnalysisTable'),
               ('proc_DetectorIntercalibrationSetTable', 'intercalibration', 'proc_DetectorIntercalibrationTable'),
               ('proc_DetectorIntercalibrationTable', 'history', 'proc_DetectorIntercalibrationHistoryTable'),
               ('proc_DetectorIntercalibrationTable', 'detector', 'gen_DetectorTable'),
               ('proc_FitHistoryTable', 'analysis', 'meas_AnalysisTable'),
               ('proc_FitTable', 'history', 'proc_FitHistoryTable'),
               ('proc_IsotopeResultsTable', 'history', 'proc_FitHistoryTable'),
               ('proc_IsotopeResultsTable', 'isotope', 'meas_IsotopeTable'),
               ('proc_SelectedHistoriesTable', 'analysis', 'meas_AnalysisTable'),
               ('proc_SelectedHistoriesTable', 'selected_blanks', 'proc_BlanksHistoryTable'),
               ('proc_SelectedHistoriesTable', 'selected_backgrounds', 'proc_BackgroundsHistoryTable'),
               ('proc_SelectedHistoriesTable', 'selected_det_intercal', 'proc_DetectorIntercalibrationHistoryTable'),
               ('proc_SelectedHistoriesTable', 'selected_fits', 'proc_FitHistoryTable'),
               ]

def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    meta = MetaData(bind=migrate_engine)
    alter_constraints(constraints, meta, action='create')


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    meta = MetaData(bind=migrate_engine)
    alter_constraints(constraints, meta, action='drop')


def alter_constraints(constraints, meta, action='create'):
    for tan, an, tbn in constraints:
        ta = Table(tan, meta, autoload=True)
        tb = Table(tbn, meta, autoload=True)
        a = getattr(ta.c, '{}_id'.format(an))
        b = tb.c.id
        cons = ForeignKeyConstraint([a], [b])
        func = getattr(cons, action)
        try:
            func()
        except Exception, e:
            print
            print e
            print tan, an, tbn
