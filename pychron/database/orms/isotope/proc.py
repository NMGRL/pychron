#===============================================================================
# Copyright 2013 Jake Ross
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#===============================================================================

#============= enthought library imports =======================
#============= standard library imports ========================
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy import Column, Integer, String, \
    BLOB, Float, Boolean, DateTime, TIMESTAMP
from sqlalchemy.orm import relationship
#============= local library imports  ==========================

from pychron.database.core.base_orm import BaseMixin, NameMixin
# from pychron.database.core.base_orm import PathMixin, ResultsMixin, ScriptTable
from sqlalchemy.sql.expression import func
from pychron.database.orms.isotope.util import foreignkey, stringcolumn
from pychron.experiment.utilities.identifier import make_runid
from pychron.pychron_constants import INTERPOLATE_TYPES

from util import Base


class History(object):
    @declared_attr
    def analysis_id(self):
        return foreignkey('meas_AnalysisTable')

    create_date = Column(DateTime, default=func.now())
    user = stringcolumn()


class HistoryMixin(BaseMixin, History):
    pass


class proc_AnalysisGroupTable(Base, NameMixin):
    create_date = Column(TIMESTAMP, default=func.now())
    last_modified = Column(TIMESTAMP)
    analyses = relationship('proc_AnalysisGroupSetTable',
                            backref='group')


class proc_AnalysisGroupSetTable(Base, BaseMixin):
    group_id = foreignkey('proc_AnalysisGroupTable')
    analysis_id = foreignkey('meas_AnalysisTable')
    analysis_type_id = foreignkey('gen_AnalysisTypeTable')


class proc_SensitivityHistoryTable(Base, HistoryMixin):
    sensitivity = relationship('proc_SensitivityTable', backref='history',
                               uselist=False)
    selected = relationship('proc_SelectedHistoriesTable',
                            backref='selected_sensitivity',
                            uselist=False)


class proc_SensitivityTable(Base, BaseMixin):
    value = Column(Float(32))
    error = Column(Float(32))
    history_id = foreignkey('proc_SensitivityHistoryTable')


class proc_TagTable(Base):
    __tablename__ = 'proc_TagTable'
    name = Column(String(40), primary_key=True)
    create_date = Column(DateTime, default=func.now())
    user = stringcolumn()

    omit_ideo = Column(Boolean)
    omit_spec = Column(Boolean)
    omit_iso = Column(Boolean)
    omit_series = Column(Boolean)

    analyses = relationship('meas_AnalysisTable', backref='tag_item')


class proc_ArArHistoryTable(Base, HistoryMixin):
    arar_result = relationship('proc_ArArTable', backref='history',
                               uselist=False)
    selected = relationship('proc_SelectedHistoriesTable',
                            backref='selected_arar',
                            uselist=False)


class proc_ArArTable(Base, BaseMixin):
    history_id = foreignkey('proc_ArArHistoryTable')
    age = Column(Float)
    age_err = Column(Float)
    age_err_wo_j = Column(Float)

    k39 = Column(Float)
    k39_err = Column(Float)
    ca37 = Column(Float)
    ca37_err = Column(Float)
    cl36 = Column(Float)
    cl36_err = Column(Float)

    Ar40 = Column(Float)
    Ar40_err = Column(Float)
    Ar39 = Column(Float)
    Ar39_err = Column(Float)
    Ar38 = Column(Float)
    Ar38_err = Column(Float)
    Ar37 = Column(Float)
    Ar37_err = Column(Float)
    Ar36 = Column(Float)
    Ar36_err = Column(Float)

    rad40 = Column(Float)
    rad40_err = Column(Float)


class proc_InterpretedAgeGroupHistoryTable(Base, BaseMixin):
    project_id = foreignkey('gen_ProjectTable')
    name = stringcolumn(80)
    create_date = Column(DateTime, default=func.now())

    interpreted_ages = relationship('proc_InterpretedAgeGroupSetTable', backref='group')


class proc_InterpretedAgeGroupSetTable(Base, BaseMixin):
    interpreted_age_id = foreignkey('proc_InterpretedAgeHistoryTable')
    group_id = foreignkey('proc_InterpretedAgeGroupHistoryTable')


class proc_InterpretedAgeSetTable(Base, BaseMixin):
    interpreted_age_id = foreignkey('proc_InterpretedAgeTable')
    analysis_id = foreignkey('meas_AnalysisTable')
    forced_plateau_step = Column(Boolean)
    plateau_step = Column(Boolean)
    tag = stringcolumn(80)


class proc_InterpretedAgeHistoryTable(Base, BaseMixin):
    create_date = Column(DateTime, default=func.now())
    user = stringcolumn()

    interpreted_age = relationship('proc_InterpretedAgeTable', backref='history', uselist=False)
    identifier = stringcolumn(80)
    selected = relationship('gen_LabTable',
                            backref='selected_interpreted_age',
                            uselist=False)

    group_sets = relationship('proc_InterpretedAgeGroupSetTable', backref='history')


class proc_InterpretedAgeTable(Base, BaseMixin):
    history_id = foreignkey('proc_InterpretedAgeHistoryTable')
    age_kind = stringcolumn(32)
    kca_kind = stringcolumn(32)

    age = Column(Float)
    age_err = Column(Float)
    display_age_units = stringcolumn(2)

    kca = Column(Float)
    kca_err = Column(Float)
    # wtd_kca = Column(Float)
    # wtd_kca_err = Column(Float)

    # arith_kca = Column(Float)
    # arith_kca_err = Column(Float)
    mswd = Column(Float)

    age_error_kind = stringcolumn(80)
    include_j_error_in_mean = Column(Boolean)
    include_j_error_in_plateau = Column(Boolean)
    include_j_error_in_individual_analyses = Column(Boolean)

    sets = relationship('proc_InterpretedAgeSetTable', backref='analyses')


class proc_BlanksSetTable(Base, BaseMixin):
    blanks_id = foreignkey('proc_BlanksTable')
    blank_analysis_id = foreignkey('meas_AnalysisTable')
    set_id = Column(Integer)


class proc_BlanksHistoryTable(Base, HistoryMixin):
    blanks = relationship('proc_BlanksTable', backref='history')
    selected = relationship('proc_SelectedHistoriesTable',
                            backref='selected_blanks',
                            uselist=False)


class proc_BlanksTable(Base, BaseMixin):
    history_id = foreignkey('proc_BlanksHistoryTable')
    user_value = Column(Float)
    user_error = Column(Float)
    use_set = Column(Boolean)
    isotope = stringcolumn()

    fit = stringcolumn()
    error_type = stringcolumn(default='SD')

    set_id = Column(Integer)
    preceding_id = foreignkey('meas_AnalysisTable')

    def make_summary(self):
        f = self.fit
        if not f in INTERPOLATE_TYPES:
            f = self.fit[:1].upper()
        s = '{}{}'.format(self.isotope, f)
        if self.preceding_id:
            p = self.preceding_analysis
            rid = make_runid(p.labnumber.identifier, p.aliquot, p.step)
            s = '{} ({})'.format(s, rid)
        return s


class proc_BackgroundsSetTable(Base, BaseMixin):
    backgrounds_id = foreignkey('proc_BackgroundsTable')
    background_analysis_id = foreignkey('meas_AnalysisTable')
    set_id = Column(Integer)


class proc_BackgroundsHistoryTable(Base, HistoryMixin):
    backgrounds = relationship('proc_BackgroundsTable',
                               backref='history')
    selected = relationship('proc_SelectedHistoriesTable',
                            backref='selected_backgrounds',
                            uselist=False)


class proc_BackgroundsTable(Base, BaseMixin):
    history_id = foreignkey('proc_BackgroundsHistoryTable')
    user_value = Column(Float)
    user_error = Column(Float)
    use_set = Column(Boolean)
    isotope = stringcolumn()
    fit = stringcolumn()
    error_type = stringcolumn(default='SD')
    set_id = Column(Integer)


class proc_DetectorIntercalibrationHistoryTable(Base, HistoryMixin):
    detector_intercalibrations = relationship('proc_DetectorIntercalibrationTable',
                                              backref='history')
    # convience
    #     detector_intercalibraion = detector_intercalibrations

    selected = relationship('proc_SelectedHistoriesTable',
                            backref='selected_detector_intercalibration',
                            uselist=False)


class proc_DetectorIntercalibrationTable(Base, BaseMixin):
    history_id = foreignkey('proc_DetectorIntercalibrationHistoryTable')
    detector_id = foreignkey('gen_DetectorTable')
    user_value = Column(Float)
    user_error = Column(Float)
    fit = stringcolumn()
    error_type = stringcolumn(default='SD')
    set_id = Column(Integer)


class proc_DetectorIntercalibrationSetTable(Base, BaseMixin):
    intercalibration_id = foreignkey('proc_DetectorIntercalibrationTable')
    ic_analysis_id = foreignkey('meas_AnalysisTable')
    set_id = Column(Integer)


class proc_DetectorParamHistoryTable(Base, HistoryMixin):
    detector_params = relationship('proc_DetectorParamTable',
                                   backref='history')

    selected = relationship('proc_SelectedHistoriesTable',
                            backref='selected_detector_param',
                            uselist=False)


class proc_DetectorParamTable(Base, BaseMixin):
    history_id = foreignkey('proc_DetectorParamHistoryTable')
    disc = Column(Float)
    disc_error = Column(Float)
    detector_id = foreignkey('gen_DetectorTable')

    #@todo: add refmass to detector param table
    refmass = 35.9675


#     selected = relationship('proc_SelectedHistoriesTable',
#                             backref='selected_detector_param',
#                             uselist=False
#                             )
class proc_FigurePrefTable(Base, BaseMixin):
    figure_id = foreignkey('proc_FigureTable')
    xbounds = Column(String(80))
    ybounds = Column(String(80))
    options = Column(BLOB)
    kind = Column(String(40))


class proc_FigureLabTable(Base, BaseMixin):
    figure_id = foreignkey('proc_FigureTable')
    lab_id = foreignkey('gen_LabTable')


class proc_FigureTable(Base, NameMixin):
    create_date = Column(DateTime, default=func.now())
    user = stringcolumn()
    project_id = foreignkey('gen_ProjectTable')

    labnumbers = relationship('proc_FigureLabTable', backref='figure')
    analyses = relationship('proc_FigureAnalysisTable', backref='figure')
    preference = relationship('proc_FigurePrefTable', backref='figure',
                              uselist=False)


class proc_FigureAnalysisTable(Base, BaseMixin):
    figure_id = foreignkey('proc_FigureTable')
    analysis_id = foreignkey('meas_AnalysisTable')
    status = Column(Integer)
    graph = Column(Integer)
    group = Column(Integer)

    analysis = relationship('meas_AnalysisTable', uselist=False)


class proc_FitHistoryTable(Base, HistoryMixin):
    fits = relationship('proc_FitTable', backref='history')
    results = relationship('proc_IsotopeResultsTable', backref='history')
    selected = relationship('proc_SelectedHistoriesTable',
                            backref='selected_fits',
                            uselist=False)


class proc_FitTable(Base, BaseMixin):
    history_id = foreignkey('proc_FitHistoryTable')
    isotope_id = foreignkey('meas_IsotopeTable')

    fit = stringcolumn()
    error_type = stringcolumn(default='SD')
    filter_outliers = Column(Boolean)
    filter_outlier_iterations = Column(Integer, default=1)
    filter_outlier_std_devs = Column(Integer, default=1)
    include_baseline_error = Column(Boolean)

    def make_summary(self):
        f = self.fit[:1].upper()
        s = '{}{}'.format(self.isotope.molecular_weight.name, f)
        return s


class proc_SelectedHistoriesTable(Base, BaseMixin):
    analysis_id = foreignkey('meas_AnalysisTable')
    selected_blanks_id = foreignkey('proc_BlanksHistoryTable')
    selected_backgrounds_id = foreignkey('proc_BackgroundsHistoryTable')
    selected_det_intercal_id = foreignkey('proc_DetectorIntercalibrationHistoryTable')
    selected_fits_id = foreignkey('proc_FitHistoryTable')
    selected_arar_id = foreignkey('proc_ArArHistoryTable')
    selected_det_param_id = foreignkey('proc_DetectorParamHistoryTable')
    selected_sensitivity_id = foreignkey('proc_SensitivityHistoryTable')


class proc_IsotopeResultsTable(Base, BaseMixin):
    signal_ = Column(Float(32))
    signal_err = Column(Float(32))
    isotope_id = foreignkey('meas_IsotopeTable')
    history_id = foreignkey('proc_FitHistoryTable')


class proc_NotesTable(Base, HistoryMixin):
    note = Column(BLOB)


# class proc_WorkspaceHistoryTable(Base, HistoryMixin):
#    workspace_id = foreignkey('WorkspaceTable')
#
#
# class proc_WorkspaceTable(Base, BaseMixin):
#    histories = relationship('WorkspaceHistoryTable', backref='workspace')
#    analyses = relationship('WorkspaceAnalysisSet', backref='workspace')

# class proc_WorkspaceAnalysisSet(Base, BaseMixin):
#    analysis_id = foreignkey('AnalysisTable')


class proc_WorkspaceSettings(Base, BaseMixin):
    '''
        settings is a yaml blob
    '''
    settings = BLOB()

#============= EOF =============================================
