# ===============================================================================
# Copyright 2011 Jake Ross
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
# ===============================================================================

#============= enthought library imports =======================
from traits.api import Int, Property, Str, Bool
#============= standard library imports ========================

#============= local library imports  ==========================
from pychron.database.core.database_selector import DatabaseSelector
# from pychron.database.core.base_db_result import DBResult

from pychron.database.orms.isotope.gen import gen_LabTable, \
    gen_SampleTable, gen_ProjectTable, \
    gen_MassSpectrometerTable, gen_AnalysisTypeTable
from pychron.database.orms.isotope.irrad import irrad_PositionTable, irrad_LevelTable, \
    irrad_IrradiationTable
from pychron.database.orms.isotope.meas import meas_AnalysisTable, meas_MeasurementTable

from pychron.database.core.base_results_adapter import BaseResultsAdapter
# from pychron.database.records.isotope_record import IsotopeRecord, IsotopeRecordView
from pychron.database.records.isotope_record import IsotopeRecordView
from pychron.database.core.query import IsotopeQuery
from pychron.experiment.utilities.identifier import make_aliquot_step
from pychron.pychron_constants import LINE_STR


class IsotopeResultsAdapter(BaseResultsAdapter):
    columns = [
        ('Labnumber', 'labnumber'),
        ('Aliquot', 'aliquot'),
        #('Analysis Time', 'rundate'),
        #               ('Time', 'runtime'),
        ('Analysis Time', 'rundate'),
        ('Irradiation', 'irradiation_info'),
        ('Mass Spec.', 'mass_spectrometer'),
        ('Type', 'analysis_type'),
        ('Project', 'project')]

    font = '10'
    #    rid_width = Int(50)
    aliquot_text = Property

    aliquot_width = Int(75)
    mass_spectrometer_width = Int(90)
    labnumber_width = Int(90)
    analysis_type_width = Int(100)
    rundate_width = Int(120)

    def _get_aliquot_text(self):
        return make_aliquot_step(self.item.aliquot, self.item.step)


class IsotopeAnalysisSelector(DatabaseSelector):
    title = 'Recall Analyses'

    query_table = meas_AnalysisTable
    record_view_klass = IsotopeRecordView

    query_klass = IsotopeQuery
    tabular_adapter_klass = IsotopeResultsAdapter

    lookup = {'Labnumber': ([gen_LabTable], gen_LabTable.identifier),
              'Step': ([], meas_AnalysisTable.step),
              'Aliquot': ([], meas_AnalysisTable.aliquot),
              'Sample': ([gen_LabTable, gen_SampleTable], gen_SampleTable.name),
              'Irradiation': ([gen_LabTable,
                               irrad_PositionTable,
                               irrad_LevelTable,
                               irrad_IrradiationTable], irrad_IrradiationTable.name),
              'Irradiation Level': ([gen_LabTable,
                                     irrad_PositionTable,
                                     irrad_LevelTable,
                                     irrad_IrradiationTable], irrad_LevelTable.name),
              'Irradiation Position': ([gen_LabTable,
                                        irrad_PositionTable,
                                        irrad_LevelTable,
                                        irrad_IrradiationTable], irrad_PositionTable.position),
              'Run Date/Time': ([], meas_AnalysisTable.analysis_timestamp),
              'Project': ([gen_LabTable, gen_SampleTable, gen_ProjectTable, ], gen_ProjectTable.name),
              'Mass Spectrometer': ([meas_MeasurementTable, gen_MassSpectrometerTable], gen_MassSpectrometerTable.name),
              'Analysis Type': ([meas_MeasurementTable, gen_AnalysisTypeTable], gen_AnalysisTypeTable.name)}

    mass_spectrometer = Str('Spectrometer')
    mass_spectrometers = Property
    analysis_type = Str('Analysis Type')
    analysis_types = Property

    omit_invalid = Bool(True)

    def set_columns(self, include=None, exclude=None, append=None):
        ta = self.tabular_adapter
        cols = ta.columns
        if append:
            if len(append[0]) == 3:
                for _, n, w in append:
                    ta.add_trait('{}_width'.format(n), Int(w))
                cols.extend([c[:2] for c in append])
            else:
                cols.extend(append)

        if exclude:
            cols = [c for c in cols if c[1] not in exclude]

        self.tabular_adapter.columns = cols

    def _record_factory(self, idn):
        if isinstance(idn, meas_AnalysisTable):
            dbr = idn
        elif isinstance(idn, str):
            uuid = idn
        else:
            uuid = idn.uuid
            dbr = self.db.get_analysis(uuid, key='uuid')

        return self.record_klass(_dbrecord=dbr)

    def _get_selector_records(self, queries=None, limit=None, use_filters=True, **kw):
        with self.db.session_ctx() as sess:
            q = sess.query(meas_AnalysisTable)

            if self.omit_invalid:
                q = q.filter(meas_AnalysisTable.tag != 'invalid')

            if queries and use_filters:
                qs = self._build_filters()
                if qs:
                    queries = queries + qs

            return self._get_records(q, queries, limit, timestamp='analysis_timestamp')

    def _get_mass_spectrometers(self):
        db = self.db
        mas = ['Spectrometer', LINE_STR]
        ms = db.get_mass_spectrometers()
        if ms:
            mas += [m.name for m in ms]
        return mas

    def _get_analysis_types(self):
        db = self.db
        ats = ['Analysis Type', LINE_STR]
        ai = db.get_analysis_types()
        if ai:
            ats += [aii.name.capitalize() for aii in ai]
        return ats

    def _analysis_type_changed(self):
        self._refresh_results()

    def _mass_spectrometer_changed(self):
        self._refresh_results()

    def _refresh_results(self):
        import inspect
        stack = inspect.stack()
        self.debug('refresh results by {}'.format(stack[1][3]))
        self.execute_query()

    def _build_filters(self):
        ma = self.mass_spectrometer
        an = self.analysis_type
        qs = []

        if ma not in ('Spectrometer', LINE_STR):
            q = self.query_factory(parameter='Mass Spectrometer', criterion=ma)
            qs.append(q)

        if an not in ('Analysis Type', LINE_STR):
            q = self.query_factory(parameter='Analysis Type', criterion=an)
            qs.append(q)

        return qs

        # ============= EOF =============================================

