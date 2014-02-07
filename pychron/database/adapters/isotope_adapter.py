#===============================================================================
# Copyright 2012 Jake Ross
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

from traits.api import Long, HasTraits, Date, Float, Str, Int
from traitsui.api import View, Item, HGroup
#============= standard library imports ========================
from cStringIO import StringIO
import hashlib

from sqlalchemy.sql.expression import and_, func, not_
from sqlalchemy.orm.exc import NoResultFound

#============= local library imports  ==========================
from pychron.database.core.functions import delete_one
from pychron.database.core.database_adapter import DatabaseAdapter
from pychron.database.selectors.isotope_selector import IsotopeAnalysisSelector

#spec_
from pychron.database.orms.isotope.spec import spec_MassCalHistoryTable, spec_MassCalScanTable

# med_
from pychron.database.orms.isotope.med import med_ImageTable, med_SnapshotTable

# flux_
from pychron.database.orms.isotope.flux import flux_FluxTable, flux_HistoryTable, flux_MonitorTable


# loading_
from pychron.database.orms.isotope.loading import loading_LoadTable, loading_PositionsTable

# gen_
from pychron.database.orms.isotope.gen import gen_LoadHolderTable, gen_DetectorTable, \
    gen_ExtractionDeviceTable, gen_ProjectTable, \
    gen_MolecularWeightTable, gen_MaterialTable, gen_MassSpectrometerTable, \
    gen_SampleTable, gen_LabTable, gen_AnalysisTypeTable, gen_UserTable, \
    gen_ImportTable, gen_SensitivityTable

# irrad_
from pychron.database.orms.isotope.irrad import irrad_HolderTable, irrad_ProductionTable, irrad_IrradiationTable, \
    irrad_ChronologyTable, irrad_LevelTable, irrad_PositionTable
# meas_
from pychron.database.orms.isotope.meas import meas_AnalysisTable, \
    meas_ExperimentTable, meas_ExtractionTable, meas_IsotopeTable, meas_MeasurementTable, \
    meas_SpectrometerParametersTable, meas_SpectrometerDeflectionsTable, \
    meas_SignalTable, meas_PeakCenterTable, meas_PositionTable, \
    meas_ScriptTable, meas_MonitorTable

# proc_
from pychron.database.orms.isotope.proc import proc_DetectorIntercalibrationHistoryTable, \
    proc_DetectorIntercalibrationTable, proc_SelectedHistoriesTable, \
    proc_BlanksTable, proc_BackgroundsTable, proc_BlanksHistoryTable, proc_BackgroundsHistoryTable, \
    proc_IsotopeResultsTable, proc_FitHistoryTable, \
    proc_FitTable, proc_DetectorParamTable, proc_NotesTable, proc_FigureTable, proc_FigureAnalysisTable, \
    proc_FigurePrefTable, proc_TagTable, proc_ArArTable, proc_InterpretedAgeHistoryTable, proc_InterpretedAgeSetTable, \
    proc_InterpretedAgeGroupHistoryTable, proc_InterpretedAgeGroupSetTable, proc_FigureLabTable, proc_SensitivityHistoryTable, proc_SensitivityTable

from pychron.pychron_constants import ALPHAS


class InterpretedAge(HasTraits):
    create_date = Date
    id = Long

    sample = Str
    identifier = Str
    material = Str
    irradiation = Str

    age = Float
    age_err = Float
    wtd_kca = Float
    wtd_kca_err = Float

    age_kind = Str
    mswd = Float
    nanalyses = Int

    def traits_view(self):
        return View(HGroup(Item('age_kind',
                                style='readonly', show_label=False),
                           Item('age', style='readonly'),
                           Item('age_err', style='readonly'),
                           Item('mswd', style='readonly', label='MSWD')))


class IsotopeAdapter(DatabaseAdapter):
    """
        new style adapter
        be careful with super methods you use they may deprecate

        using decorators is the new model
    """

    selector_klass = IsotopeAnalysisSelector

    def set_analysis_sensitivity(self, analysis, v, e):
        hist = proc_SensitivityHistoryTable()
        hist.analysis_id = analysis.id
        self._add_item(hist)

        sens = proc_SensitivityTable(value=float(v),
                                     error=float(e))
        hist.sensitivity = sens
        self._add_item(sens)

        analysis.selected_histories.selected_sensitivity = hist

    def save_flux(self, identifier, v, e, inform=True):

        with self.session_ctx():
            dbln = self.get_labnumber(identifier)
            if dbln:
                dbpos = dbln.irradiation_position
                dbhist = self.add_flux_history(dbpos)
                dbflux = self.add_flux(float(v), float(e))
                dbflux.history = dbhist
                dbln.selected_flux_history = dbhist
                msg = u'Flux for {} {} \u00b1{} saved to database'.format(identifier, v, e)
                if inform:
                    self.information_dialog(msg)
                else:
                    self.debug(msg)

    def interpreted_age_factory(self, hi):
        dbln = self.get_labnumber(hi.identifier)
        sample = None
        irrad = None
        material = None
        if dbln:
            if dbln.sample:
                sample = dbln.sample.name
                dbmat = dbln.sample.material
                if dbmat:
                    material = dbmat.name

            pos = dbln.irradiation_position
            if pos:
                level = pos.level
                irrad = level.irradiation
                irrad = '{}{} {}'.format(irrad.name, level.name, pos.position)
        ia = hi.interpreted_age

        if ia.age_kind == 'Plateau':
            n = len(filter(lambda x: x.plateau_step, ia.sets))
        else:
            n = len(ia.sets)

        it = InterpretedAge(create_date=hi.create_date,
                            id=hi.id,
                            age=ia.age,
                            age_err=ia.age_err,
                            wtd_kca=ia.wtd_kca or 0,
                            wtd_kca_err=ia.wtd_kca_err or 0,
                            mswd=ia.mswd,
                            age_kind=ia.age_kind,
                            identifier=hi.identifier,
                            sample=sample or '',
                            irradiation=irrad or '',
                            material=material or '',
                            nanalyses=n,
                            name='{} - {}'.format(hi.create_date, ia.age_kind))

        return it

    def get_interpreted_age_group_history(self, gid):
        return self._retrieve_item(proc_InterpretedAgeGroupHistoryTable,
                                   gid, key='id')


    def get_interpreted_age_groups(self, project):
        with self.session_ctx() as sess:
            q = sess.query(proc_InterpretedAgeGroupHistoryTable)
            q = q.join(gen_ProjectTable)

            q = q.filter(gen_ProjectTable.name == project)

            try:
                return q.all()
            except NoResultFound:
                pass

    def get_interpreted_age_histories(self, values, key='identifier'):
        with self.session_ctx() as sess:
            q = sess.query(proc_InterpretedAgeHistoryTable)

            attr = getattr(proc_InterpretedAgeHistoryTable, key)
            q = q.filter(attr.in_(values))

            try:
                return q.all()
            except NoResultFound:
                pass

    def get_project_analysis_count(self, projects):
        if not hasattr(projects, '__iter__'):
            projects = (projects,)
        with self.session_ctx() as sess:
            q = sess.query(meas_AnalysisTable)
            q = q.join(gen_LabTable)
            q = q.join(gen_SampleTable)
            q = q.join(gen_ProjectTable)
            q = q.filter(gen_ProjectTable.name.in_(projects))
            try:
                return int(q.count())
            except NoResultFound:
                pass

    def get_project_figures(self, projects):
        if not hasattr(projects, '__iter__'):
            projects = (projects,)

        with self.session_ctx() as sess:
            q = sess.query(proc_FigureTable)
            q = q.join(gen_ProjectTable)
            q = q.filter(gen_ProjectTable.name.in_(projects))
            try:
                return q.all()
            except NoResultFound:
                pass

    def get_labnumber_figures(self, identifiers):
        if not hasattr(identifiers, '__iter__'):
            identifiers = (identifiers,)

        with self.session_ctx() as sess:
            q = sess.query(proc_FigureTable)
            q = q.join(proc_FigureLabTable)
            q = q.join(gen_LabTable)
            q = q.filter(gen_LabTable.identifier.in_(identifiers))
            try:
                return q.all()
            except NoResultFound:
                pass

    def get_preceding(self, post, ms, atype='blank_unknown'):
        with self.session_ctx() as sess:
            q = sess.query(meas_AnalysisTable)
            q = q.join(meas_MeasurementTable)
            q = q.join(gen_AnalysisTypeTable)
            q = q.join(gen_MassSpectrometerTable)

            q = q.filter(and_(
                gen_AnalysisTypeTable.name == atype,
                gen_MassSpectrometerTable.name == ms,
                meas_AnalysisTable.analysis_timestamp < post))

            q = q.order_by(meas_AnalysisTable.analysis_timestamp.desc())
            try:
                return q.first()
            except NoResultFound:
                pass

    def get_date_range_analyses(self, start, end,
                                labnumber=None,
                                atype=None,
                                spectrometer=None,
                                extract_device=None,
                                limit=None,
                                exclude_uuids=None):

        with self.session_ctx() as sess:
            q = sess.query(meas_AnalysisTable)
            q = q.join(meas_MeasurementTable)

            if atype:
                q = q.join(gen_AnalysisTypeTable)
            if labnumber:
                q = q.join(gen_LabTable)
            if spectrometer:
                q = q.join(gen_MassSpectrometerTable)
            if extract_device:
                q = q.join(meas_ExtractionTable, gen_ExtractionDeviceTable)

            if atype:
                q = q.filter(gen_AnalysisTypeTable.name == atype)
            if labnumber:
                q = q.filter(gen_LabTable.identifier == labnumber)
            if spectrometer:
                q = q.filter(gen_MassSpectrometerTable.name == spectrometer)
            if extract_device:
                q = q.filter(gen_ExtractionDeviceTable.name == extract_device)

            q = q.filter(and_(meas_AnalysisTable.analysis_timestamp <= end,
                              meas_AnalysisTable.analysis_timestamp >= start))
            if exclude_uuids:
                q = q.filter(not_(meas_AnalysisTable.uuid.in_(exclude_uuids)))

            q = q.order_by(meas_AnalysisTable.analysis_timestamp.desc())
            if limit:
                q = q.limit(limit)

            return self._query_all(q)

    #def count_sample_analyses(self, *args, **kw):
    #    return self._get_sample_analyses('count', *args, **kw)
    def get_labnumber_analyses(self, lns, low_post=None, **kw):
        if not hasattr(lns, '__iter__'):
            lns = (lns, )

        with self.session_ctx() as sess:
            q = sess.query(meas_AnalysisTable)
            q = q.join(gen_LabTable)
            q = q.filter(gen_LabTable.identifier.in_(lns))
            if low_post:
                q = q.filter(meas_AnalysisTable.analysis_timestamp >= low_post)

            return self._get_paginated_analyses(q, **kw)

    def _get_paginated_analyses(self, q, limit=None, offset=None,
                                include_invalid=False):
        if not include_invalid:
            q = q.filter(meas_AnalysisTable.tag != 'invalid')

        q = q.order_by(meas_AnalysisTable.analysis_timestamp.asc())

        tc = int(q.count())

        if limit:
            q = q.limit(limit)
        if offset:

            if offset < 0:
                offset = max(0, tc + offset)

            q = q.offset(offset)

        return self._query_all(q), tc

    def get_sample_analyses(self, samples, projects, **kw):
        if not isinstance(samples, (list, tuple)):
            samples = (samples,)

        with self.session_ctx() as sess:
            q = sess.query(meas_AnalysisTable)
            q = q.join(gen_LabTable)
            q = q.join(gen_SampleTable)
            q = q.join(gen_ProjectTable)

            q = q.filter(gen_SampleTable.name.in_(samples))
            q = q.filter(gen_ProjectTable.name.in_(projects))

            return self._get_paginated_analyses(q, **kw)

            #return self._get_sample_analyses('all', *args, **kw)

    #def _get_sample_analyses(self, f, samples, projects, limit=None, offset=None,
    #                         include_invalid=False):
    #    if not isinstance(samples, (list, tuple)):
    #        samples = (samples,)
    #
    #    with self.session_ctx() as sess:
    #        q = sess.query(meas_AnalysisTable)
    #        q = q.join(gen_LabTable)
    #        q = q.join(gen_SampleTable)
    #        q = q.join(gen_ProjectTable)
    #
    #        if not include_invalid:
    #            q = q.filter(meas_AnalysisTable.tag != 'invalid')
    #
    #        q = q.filter(gen_SampleTable.name.in_(samples))
    #        q = q.filter(gen_ProjectTable.name.in_(projects))
    #        q = q.order_by(meas_AnalysisTable.analysis_timestamp.asc())
    #
    #        tc = int(q.count())
    #
    #        if limit:
    #            q = q.limit(limit)
    #        if offset:
    #            q = q.offset(offset)
    #
    #        return getattr(q, f)(), tc

    def get_analyses_date_range(self, mi, ma,
                                analysis_type=None,
                                mass_spectrometer=None,
                                extract_device=None,
                                project=None,
                                exclude_invalid=True):
        ed = extract_device
        ms = mass_spectrometer
        at = analysis_type
        pr = project
        with self.session_ctx() as sess:
            q = sess.query(meas_AnalysisTable)
            q = q.join(gen_LabTable)
            q = q.join(meas_MeasurementTable)

            if ms:
                q = q.join(gen_MassSpectrometerTable)

            if ed:
                q = q.join(meas_ExtractionTable)
                q = q.join(gen_ExtractionDeviceTable)
            if at:
                q = q.join(gen_AnalysisTypeTable)
            if pr:
                q = q.join(gen_SampleTable)
                q = q.join(gen_ProjectTable)

            if ms:
                q = q.filter(gen_MassSpectrometerTable.name == ms)
            if ed:
                q = q.filter(gen_ExtractionDeviceTable.name == ed)
            if at:
                q = q.filter(gen_AnalysisTypeTable.name == at)
            if pr:
                q = q.filter(gen_ProjectTable.name == pr)

            q = q.filter(and_(meas_AnalysisTable.analysis_timestamp >= mi,
                              meas_AnalysisTable.analysis_timestamp <= ma))

            if exclude_invalid:
                q = q.filter(meas_AnalysisTable.tag != 'invalid')
            return q.all()

    def add_interpreted_age_group_history(self, name, project=None):
        project = self.get_project(project)

        if project:
            obj = proc_InterpretedAgeGroupHistoryTable(name=name)
            obj.project_id = project.id
            self._add_item(obj)
            return obj

    def add_interpreted_age_group_set(self, hist, interpreted_age_id, **kw):
        obj = proc_InterpretedAgeGroupSetTable(**kw)

        obj.group = hist
        obj.interpreted_age_id = interpreted_age_id
        self._add_item(obj)
        return obj

    def add_history(self, dbrecord, kind):
        func = getattr(self, 'add_{}_history'.format(kind))
        history = func(dbrecord, user=self.save_username)
        #        history = db.add_blanks_history(dbrecord, user=db.save_username)

        # set analysis' selected history
        sh = self.add_selected_histories(dbrecord)
        setattr(sh, 'selected_{}'.format(kind), history)
        #db.sess.flush()
        #        sh.selected_blanks = history
        return history

    def add_mass_calibration_history(self, spectrometer):
        spec = self.get_mass_spectrometer(spectrometer)
        if spec:
            hist = spec_MassCalHistoryTable()
            hist.spectrometer_id = spec.id
            self._add_item(hist)
            return hist

    def add_mass_calibration_scan(self, hist, iso, **kw):
        s = spec_MassCalScanTable(**kw)

        iso = self.get_molecular_weight(iso)

        s.history_id = hist.id
        s.molecular_weight_id = iso.id

        self._add_item(s)
        return s

    def add_arar_history(self, analysis, **kw):
        hist = self._add_history('ArAr', analysis, **kw)
        return hist

    def add_arar(self, hist, **kw):
        a = proc_ArArTable(**kw)
        hist.arar_result = a

        self._add_item(a)

        return a

    def add_load(self, name, **kw):
        l = loading_LoadTable(name=name, **kw)
        self._add_item(l)
        return l

    def add_load_position(self, labnumber, **kw):
        lp = loading_PositionsTable(**kw)

        ln = self.get_labnumber(labnumber)
        if ln:
            lp.lab_identifier = ln.identifier

        self._add_item(lp)
        return lp

    def get_loadtable(self, name=None):
        lt = None
        #         with session(sess) as s:
        if name is not None:
            lt = self._retrieve_item(loading_LoadTable, name)
        else:
            with self.session_ctx() as s:
                q = s.query(loading_LoadTable)
                #             q = self.get_query(loading_LoadTable)
                if q:
                    q = q.order_by(loading_LoadTable.create_date.desc())
                    try:
                        lt = q.first()
                    except Exception, e:
                        import traceback

                        traceback.print_exc()

        return lt

    #===============================================================================
    #
    #===============================================================================
    def clone_record(self, a):
        sess = self.new_session()
        q = sess.query(meas_AnalysisTable)
        q = q.filter(meas_AnalysisTable.id == a.id)
        r = q.one()

        return r

    #===========================================================================
    # adders
    #===========================================================================

    def _add_history(self, name, analysis, **kw):
        name = 'proc_{}HistoryTable'.format(name)
        #mod_path = 'pychron.database.orms.isotope.proc'
        #mod = __import__(mod_path, fromlist=[name])
        #table = getattr(mod, name)
        table = self.__import_proctable(name)
        #table = globals()['proc_{}HistoryTable'.format(name)]
        analysis = self.get_analysis(analysis)
        h = table(analysis=analysis, **kw)
        self._add_item(h)
        return h

    def _add_set(self, name, key, analysis, idname=None, **kw):
        """
            name: e.g Blanks
            key:
        """

        name = 'proc_{}SetTable'.format(name)
        table = self.__import_proctable(name)
        nset = table(**kw)

        #pa = getattr(self, 'get_{}'.format(key))(value)
        analysis = self.get_analysis(analysis)
        if analysis:
            if idname is None:
                idname = key
            setattr(nset, '{}_analysis_id'.format(idname), analysis.id)

            #analysis.blanks_sets.append(nset)
            #nset.analysis
            #nset.analyses.append(analysis)

            # if value:
            #     value.sets.append(nset)
            #    if idname is None:
        #        idname = key
        #    setattr(nset, '{}_analysis_id'.format(idname), analysis.id)
        #
        #if pa:
        #    setattr(nset, '{}_id'.format(name.lower()), pa.id)

        self._add_item(nset)
        return nset

    def __import_proctable(self, name):
        mod_path = 'pychron.database.orms.isotope.proc'
        mod = __import__(mod_path, fromlist=[name])
        table = getattr(mod, name)
        return table

    def _add_series_item(self, name, key, history, **kw):
        name = 'proc_{}Table'.format(name)
        #item = globals()['proc_{}Table'.format(name)](**kw)
        table = self.__import_proctable(name)
        item = table(**kw)

        history = getattr(self, 'get_{}_history'.format(key))(history, )
        if history:
            try:
                item.history = history
                #item.history_id = history.id
            #                 getattr(history, key).append(item)
            except AttributeError, e:
                self.debug('add_series_item key={}, error={}'.format(key, e))
                setattr(history, key, item)
            self._add_item(item)

        return item

    def add_tag(self, name, **kw):
        tag = proc_TagTable(name=name, **kw)
        return self._add_unique(tag, 'tag', name)

    def add_import(self, **kw):
        dbimport = gen_ImportTable(**kw)
        self._add_item(dbimport)
        return dbimport

    def add_snapshot(self, path, **kw):
        dbsnap = med_SnapshotTable(path, **kw)
        self._add_item(dbsnap)
        return dbsnap

    def add_image(self, name, image=None):
        if image is not None:
            if not isinstance(image, str):
                buf = StringIO()
                image.save(buf)
                image = buf.getvalue()

        dbim = med_ImageTable(name=name, image=image)
        self._add_item(dbim)
        return dbim

    def add_monitor(self, analysis, **kw):
        dbm = meas_MonitorTable(**kw)
        analysis = self.get_analysis(analysis)
        if analysis:
            dbm.analysis = analysis
            #dbm.analysis_id = analysis.id
            #             analysis.monitors.append(dbm)
        self._add_item(dbm)
        return dbm

    def add_analysis_position(self, extraction, pos, **kw):
        try:
            pos = int(pos)
            dbpos = meas_PositionTable(position=pos, **kw)
            if extraction:
                dbpos.extraction_id = extraction.id
                #             extraction.positions.append(dbpos)
            self._add_item(dbpos)
            return dbpos
        except (ValueError, TypeError), e:
            pass

    def add_note(self, analysis, note, **kw):
        analysis = self.get_analysis(analysis)
        obj = proc_NotesTable(note=note, user=self.save_username)
        if analysis:
            note.analysis = analysis
            #analysis.notes.append(obj)
        return obj

    def add_interpreted_age_history(self, labnumber, **kw):
        name = 'proc_InterpretedAgeHistoryTable'
        table = self.__import_proctable(name)

        labnumber = self.get_labnumber(labnumber)
        t = table(identifier=labnumber.identifier, **kw)
        labnumber.selected_interpreted_age = t

        self._add_item(t)

        return t

    def add_interpreted_age(self, history, **kw):
        return self._add_series_item('InterpretedAge', 'interpreted_age', history, **kw)

    def add_interpreted_age_set(self, interpreted_age, analysis, **kw):
        item = proc_InterpretedAgeSetTable(analysis=analysis,
                                           interpreted_age_id=interpreted_age.id,
                                           **kw)
        return self._add_item(item)
        #return self._add_set('InterpretedAge', 'interpreted_age',
        #                     interpreted_age, analysis, **kw)

    def add_blanks_history(self, analysis, **kw):
        return self._add_history('Blanks', analysis, **kw)

    def add_blanks(self, history, **kw):
        return self._add_series_item('Blanks', 'blanks', history, **kw)

    def add_blanks_set(self, blank, analysis, **kw):
        return self._add_set('Blanks', 'blank', blank, analysis, **kw)

    def add_backgrounds_history(self, analysis, **kw):
        return self._add_history('Backgrounds', analysis, **kw)

    def add_backgrounds(self, history, **kw):
        return self._add_series_item('Backgrounds', 'backgrounds', history, **kw)

    def add_backgrounds_set(self, background, analysis, **kw):
        return self._add_set('Backgrounds', 'background', background, analysis, **kw)

    def add_detector(self, name, **kw):
        det = gen_DetectorTable(name=name, **kw)
        return self._add_unique(det, 'detector', name, )

    def add_detector_parameter_history(self, analysis, **kw):
        return self._add_history('DetectorParam', analysis, **kw)

    def add_detector_parameter(self, history, detector, **kw):
        obj = proc_DetectorParamTable(**kw)
        if history:
            obj.history = history

        detector = self.get_detector(detector)
        obj.detector = detector
        #    obj.history_id = history.id

        self._add_item(obj)

        return obj

    def add_detector_intercalibration_history(self, analysis, **kw):
        return self._add_history('DetectorIntercalibration', analysis, **kw)

    def add_detector_intercalibration(self, history, detector, **kw):
        a = self._add_series_item('DetectorIntercalibration',
                                  'detector_intercalibrations', history, **kw)
        if a:
            detector = self.get_detector(detector)
            #if detector:
            a.detector = detector
            #a.detector_id = detector.id
            #             detector.intercalibrations.append(a)

        return a

    def add_detector_intercalibration_set(self, analysis, **kw):
        return self._add_set('DetectorIntercalibration', 'detector_intercalibration',
                             analysis, idname='ic', **kw)

    def add_experiment(self, name, **kw):
        exp = meas_ExperimentTable(name=name, **kw)
        self._add_item(exp)
        return exp

    def add_extraction(self, analysis, extract_device=None, **kw):
    #        ex = self._get_script('extraction', script_blob)
    #        if ex is None:
    #            ha = self._make_hash(script_blob)
        ex = meas_ExtractionTable(**kw)
        self._add_item(ex)

        analysis = self.get_analysis(analysis)
        if analysis:
            analysis.extraction = ex

        ed = self.get_extraction_device(extract_device)
        ex.extraction_device = ed
        #ex.extract_device_id = ed.id

        #             ed.extractions.append(ex)

        return ex

    def add_extraction_device(self, name, **kw):
        item = gen_ExtractionDeviceTable(name=name, **kw)
        return self._add_unique(item, 'extraction_device', name, )

    def add_figure_labnumber(self, figure, labnumber):
        labnumber = self.get_labnumber(labnumber)
        if labnumber:
            obj = proc_FigureLabTable()
            self._add_item(obj)
            obj.figure = figure
            obj.labnumber = labnumber
            return obj

    def add_figure(self, project=None, **kw):
        fig = proc_FigureTable(
            user=self.save_username,
            **kw)
        project = self.get_project(project)
        if project:
            fig.project = project

        self._add_item(fig)

        return fig

    def add_figure_preference(self, figure, **kw):
        fa = proc_FigurePrefTable(**kw)
        figure = self.get_figure(figure)
        if figure:
            self.info('adding preference to figure {}'.format(figure.name))
            fa.figure_id = figure.id
        self._add_item(fa)
        return fa

    def add_figure_analysis(self, figure, analysis, **kw):
        fa = proc_FigureAnalysisTable(**kw)
        figure = self.get_figure(figure)
        if figure:
            fa.figure = figure
            #fa.figure_id = figure.id

        analysis = self.get_analysis(analysis)
        if analysis:
            fa.analysis = analysis
            #fa.analysis_id = analysis.id

        self._add_item(fa)
        return fa


    #         if figure:
    #             figure.analyses.append(fa)
    #             if analysis:
    #                 analysis.figure_analyses.append(fa)
    # #                self._add_item(fa)
    #
    #         return fa

    def add_fit_history(self, analysis, **kw):
        kw['user'] = self.save_username
        hist = proc_FitHistoryTable(**kw)
        if analysis:
            hist.analysis = analysis
            #hist.analysis_id = analysis.id

            if analysis.selected_histories is None:
                self.add_selected_histories(analysis)

            #            analysis.fit_histories.append(hist)
            analysis.selected_histories.selected_fits = hist

        return hist

    def add_fit(self, history, isotope, **kw):
        f = proc_FitTable(**kw)
        f.history = history
        f.isotope = isotope

        #if history:
        #    f.history=history

        #if isotope:
        #    f.isotope=isotope
        self._add_item(f)
        return f

    def add_flux(self, j, j_err):
        f = flux_FluxTable(j=j, j_err=j_err)
        self._add_item(f)
        return f

    def add_flux_history(self, pos, **kw):
        ft = flux_HistoryTable(**kw)
        if pos:
            ft.position = pos
        return ft

    def add_flux_monitor(self, name, **kw):
        """

        """
        fx = flux_MonitorTable(name=name, **kw)
        return self._add_unique(fx, 'flux_monitor', name)

    def add_irradiation(self, name, chronology=None):
        chronology = self.get_irradiation_chronology(chronology)

        ir = irrad_IrradiationTable(name=name,
                                    chronology=chronology)
        self._add_item(ir)
        return ir

    def add_load_holder(self, name, **kw):
        lh = gen_LoadHolderTable(name=name, **kw)
        return self._add_unique(lh, 'load_holder', name, )

    def add_irradiation_holder(self, name, **kw):
        ih = irrad_HolderTable(name=name, **kw)
        return self._add_unique(ih, 'irradiation_holder', name, )

    def add_irradiation_production(self, **kw):
        ip = irrad_ProductionTable(**kw)
        self._add_item(ip, )
        return ip

    def add_irradiation_position(self, pos, labnumber, irrad, level, **kw):
        if labnumber:
            labnumber = self.get_labnumber(labnumber)

        irrad = self.get_irradiation(irrad, )
        if isinstance(level, (str, unicode)):
            level = next((li for li in irrad.levels if li.name == level), None)

        if level:
            dbpos = next((di for di in level.positions if di.position == pos), None)
            if not dbpos:
                dbpos = irrad_PositionTable(position=pos, **kw)

                dbpos.level = level
                self._add_item(dbpos)

            labnumber.irradiation_position = dbpos

            return dbpos

    def add_irradiation_chronology(self, chronblob):
        '''
            startdate1 starttime1%enddate1 endtime1$startdate2 starttime2%enddate2 endtime2
        '''
        ch = irrad_ChronologyTable(chronology=chronblob)
        self._add_item(ch, )
        return ch

    def add_irradiation_level(self, name, irradiation, holder, production, z=0):
        irradiation = self.get_irradiation(irradiation)
        production = self.get_irradiation_production(production)
        if irradiation:
            irn = irradiation.name
            level = next((li for li in irradiation.levels if li.name == name), None)
            if not level:
                holder = self.get_irradiation_holder(holder)
                #             irn = irradiation.name if irradiation else None
                hn = holder.name if holder else None
                self.info('adding level {}, holder={} to {}'.format(name, hn, irn))

                level = irrad_LevelTable(name=name, z=z)

                level.irradiation = irradiation
                level.holder = holder
                level.production = production

                self._add_item(level)

            return level
        else:
            self.info('no irradiation to add to as this level. irradiation={}'.format(irradiation))

    def add_isotope(self, analysis, molweight, det, **kw):
        iso = meas_IsotopeTable(**kw)
        analysis = self.get_analysis(analysis)
        iso.analysis = analysis
        det = self.get_detector(det, )
        iso.detector = det
        molweight = self.get_molecular_weight(molweight)
        iso.molecular_weight = molweight

        #if analysis:
        #    iso.analysis=analysis
        #iso.analysis_id = analysis.id
        #            analysis.isotopes.append(iso)

        #if det is not None:
        #iso.detector=det
        #iso.detector_id = det.id
        #            det.isotopes.append(iso)


        #if molweight is not None:
        #iso.molecular_weight_id = molweight.id
        #            molweight.isotopes.append(iso)

        self._add_item(iso)
        return iso

    def add_isotope_result(self, isotope, history, **kw):
        r = proc_IsotopeResultsTable(**kw)
        r.isotope = isotope
        r.history = history
        #if isotope:
        #r.isotope=isotope
        #r.isotope_id = isotope.id
        #             isotope.results.append(r)
        #if history:
        #r.history=history
        #r.history_id = history.id
        #                 history.results.append(r)
        self._add_item(r, )
        return r

    def add_measurement(self, analysis, analysis_type, mass_spec, **kw):
        meas = meas_MeasurementTable(**kw)
        #        if isinstance(analysis, str):

        self._add_item(meas, )

        an = self.get_analysis(analysis, )
        at = self.get_analysis_type(analysis_type, )
        ms = self.get_mass_spectrometer(mass_spec, )
        if an:
            an.measurement = meas

        meas.mass_spectrometer = ms
        meas.analysis_type = at
        #if at:
        #    meas.analysis_type_id = at.id
        #if ms:
        #    meas.mass_spectrometer_id = ms.id
        #
        return meas

    def add_mass_spectrometer(self, name):
        ms = gen_MassSpectrometerTable(name=name)
        return self._add_unique(ms, 'mass_spectrometer', name)

    def add_material(self, name, **kw):
        mat = gen_MaterialTable(name=name, **kw)
        return self._add_unique(mat, 'material', name)

    def add_molecular_weight(self, name, mass):
        mw = gen_MolecularWeightTable(name=name, mass=mass)
        return self._add_unique(mw, 'molecular_weight', name)

    def add_project(self, name, **kw):
        proj = gen_ProjectTable(name=name, **kw)
        return self._add_unique(proj, 'project', name, )

    def add_peak_center(self, analysis, **kw):
        pc = meas_PeakCenterTable(**kw)
        if analysis:
            analysis.peak_center = pc
        return pc

    def add_user(self, name, **kw):
        user = gen_UserTable(name=name, **kw)
        self._add_item(user)
        return user

    #    def add_user(self, name, **kw):
    #        user = gen_UserTable(name=name, **kw)
    #        if isinstance(project, str):
    #            project = self.get_project(project)
    #
    #        q = self._build_query_and(gen_UserTable, name, gen_ProjectTable, project)
    #
    #        addflag = True
    #        u = q.one()
    #        if u is not None:
    #            addflag = not (u.project == project)
    #
    #        if addflag:
    #            self.info('adding user {}'.format(name))
    #            if project is not None:
    #                project.users.append(user)
    #            self._add_item(user)
    #        return user


    def add_sample(self, name, project=None, material=None, **kw):
        with self.session_ctx() as sess:

            q = sess.query(gen_SampleTable)
            if project:
                project = self.get_project(project)
                q = q.filter(gen_SampleTable.project == project)
                #q=q.join(gen_ProjectTable)

            if material:
                material = self.get_material(material)
                q = q.filter(gen_SampleTable.material == material)
                #q=q.join(gen_MaterialTable)

            q = q.filter(gen_SampleTable.name == name)
            #if project:
            #    q=q.filter()

            #q = q.filter(and_(gen_SampleTable.name == name,
            #                  getattr(gen_SampleTable, 'material') == material,
            #                  getattr(gen_SampleTable, 'project') == project,
            #))

            try:
                sample = q.one()
            except Exception, e:
                print e, name, project, material
                sample = None

            if sample is None:
                sample = self._add_sample(name, project, material)
            else:
                materialname = material.name if material else None
                projectname = project.name if project else None

                sample_material_name = sample.material.name if sample.material else None
                sample_project_name = sample.project.name if sample.project else None
                #            print sample_material_name, sample_project_name, materialname, projectname
                if sample_material_name != materialname and \
                                sample_project_name != projectname:
                    sample = self._add_sample(name, project, material)

            return sample

    def _add_sample(self, name, project, material):
        sample = gen_SampleTable(name=name)

        project = self.get_project(project)
        material = self.get_material(material)
        sample.material = material
        sample.project = project

        #if project is not None:
        #    project.samples.append(sample)
        #
        #material = self.get_material(material)
        #if material is not None:
        #    material.samples.append(sample)

        self.info('adding sample {} project={}, material={}'.format(name,
                                                                    project.name if project else 'None',
                                                                    material.name if material else 'None', ))

        self._add_item(sample)
        return sample

    def add_script(self, name, blob):
        seed = '{}{}'.format(name, blob)
        ha = self._make_hash(seed)
        scr = self.get_script(ha, )
        if scr is None:
            scr = meas_ScriptTable(name=name, blob=blob, hash=ha)
            self._add_item(scr, )

        return scr

    def add_selected_histories(self, analysis, **kw):
        sh = analysis.selected_histories
        if sh is None:
            sh = proc_SelectedHistoriesTable(analysis_id=analysis.id)
            analysis.selected_histories = sh
        return sh

    def add_signal(self, isotope, data):
        s = meas_SignalTable(data=data)
        s.isotope = isotope
        #if isotope:
        #    s.isotope_id = isotope.id
        #            isotope.signals.append(s)
        self._add_item(s, )
        return s

    def add_spectrometer_parameters(self, meas, params):
        ha = self._make_hash(params)
        sp = self.get_spectrometer_parameters(ha, )
        if sp is None:
            sp = meas_SpectrometerParametersTable(hash=ha,
                                                  **params)

        if meas:
            meas.spectrometer_parameters = sp
            #meas.spectrometer_parameters_id = sp.id

        return sp

    def add_deflection(self, meas, det, value):
        sp = meas_SpectrometerDeflectionsTable(deflection=value)
        sp.measurement = meas
        det = self.get_detector(det)
        sp.detector = det
        #if meas:

        #sp.measurement_id = meas.id
        #             meas.deflections.append(sp)
        #det = self.get_detector(det, )
        #if det:
        #    sp.detector_id = det.id
        #                 det.deflections.append(sp)

        return sp

    def add_labnumber(self, labnumber,
                      #                      aliquot,
                      sample=None,
                      unique=True,
                      sess=None,
                      **kw):

        sample = self.get_sample(sample)
        if unique:
            ln = self.get_labnumber(labnumber)
            #print labnumber, ln, sample, ln.sample
            if ln and sample and ln.sample != sample:
                ln = None
        else:
            ln = None

        if ln is None:
            ln = gen_LabTable(identifier=labnumber, **kw)
            ln.sample = sample

            if sample is None:
                self.debug('sample {} does not exist'.format(sample))
                sname = ''
            else:
                sname = sample.name

            #if sample is not None:
            #    ln.sample_id = sample.id
            #    #                 sample.labnumbers.append(ln)
            #    sname = sample.name
            #else:
            #    self.debug('sample {} does not exist'.format(sample))
            #    sname = ''

            self.info('adding labnumber={} sample={}'.format(labnumber, sname))
            self._add_item(ln)

        return ln

    def add_analysis(self, labnumber, **kw):
    #        if isinstance(labnumber, (str, int, unicode)):
        labnumber = self.get_labnumber(labnumber, )

        anal = meas_AnalysisTable(**kw)
        if labnumber is not None:
            anal.labnumber = labnumber
            #anal.lab_id = labnumber.id
            #             labnumber.analyses.append(anal)

        self._add_item(anal)
        return anal

    def add_analysis_type(self, name):
        at = gen_AnalysisTypeTable(name=name)
        return self._add_unique(at, 'analysis_type', name, )

    def add_sensitivity(self, ms, **kw):
        si = gen_SensitivityTable(**kw)
        ms = self.get_mass_spectrometer(ms, )
        si.mass_spectrometer = ms
        #if ms is not None:
        #    si.mass_spectrometer_id = ms.id
        #             ms.sensitivities.append(si)
        return ms

    #===========================================================================
    # getters single
    #===========================================================================
    def get_arar(self, k):
        return self._retrieve_item(proc_ArArTable, k, key='hash')

    def get_last_labnumber(self, sample=None):
        with self.session_ctx() as s:
        #         sess = self.get_session()
            q = s.query(gen_LabTable)
            if sample:
                q = q.join(gen_SampleTable)
                q = q.filter(gen_SampleTable.name == sample)

            q = q.order_by(func.abs(gen_LabTable.identifier).desc())
            try:
                return q.first()
            except NoResultFound, e:
                self.debug('get last labnumber {}'.format(e))
                return

    def get_greatest_aliquot(self, ln):
        with self.session_ctx() as sess:
            if ln:
                ln = self.get_labnumber(ln)
                if not ln:
                    return
                q = sess.query(meas_AnalysisTable.aliquot)
                q = q.filter(meas_AnalysisTable.labnumber == ln)
                q = q.order_by(meas_AnalysisTable.aliquot.desc())
                result = self._query_one(q)
                if result:
                    return int(result[0])

    def get_greatest_step(self, ln, aliquot):
        """
            return greatest step for this labnumber and aliquot.
            return step as an integer. A=0, B=1...
        """
        with self.session_ctx() as sess:
            if ln:
                ln = self.get_labnumber(ln)
                if not ln:
                    return
                q = sess.query(meas_AnalysisTable.step)
                q = q.filter(meas_AnalysisTable.labnumber == ln)
                q = q.filter(meas_AnalysisTable.aliquot == aliquot)
                # q = q.order_by(cast(meas_AnalysisTable.step, INTEGER(unsigned=True)).desc())
                q = q.order_by(meas_AnalysisTable.increment.desc())
                result = self._query_one(q)
                if result:
                    step = result[0]
                    return ALPHAS.index(step) if step is not None else -1

    def get_last_analysis(self, ln=None, aliquot=None, spectrometer=None, ret=None):
        self.debug('get last analysis labnumber={}, aliquot={}, spectrometer={}'.format(ln, aliquot, spectrometer))
        with self.session_ctx() as sess:
            if ln:
                ln = self.get_labnumber(ln)
                if not ln:
                    return

            q = sess.query(meas_AnalysisTable)

            if spectrometer:
                q = q.join(meas_MeasurementTable)
                q = q.join(gen_MassSpectrometerTable)

            if ln:
                q = q.join(gen_LabTable)

            if spectrometer:
                q = q.filter(gen_MassSpectrometerTable.name == spectrometer)

            if ln:
                q = q.filter(meas_AnalysisTable.labnumber == ln)
                if aliquot:
                    q = q.filter(meas_AnalysisTable.aliquot == aliquot)

            q = q.order_by(meas_AnalysisTable.analysis_timestamp.desc())
            q = q.limit(1)
            try:
                r = q.one()
                self.debug('got last analysis {}-{}'.format(r.labnumber.identifier, r.aliquot))
                return r
            except NoResultFound, e:
                self.debug('no analyses for {}'.format(ln.identifier))
                return 0

    def get_unique_analysis(self, ln, ai, step=None):
    #         sess = self.get_session()
        with self.session_ctx() as sess:
            ln = self.get_labnumber(ln)
            if not ln:
                return

            q = sess.query(meas_AnalysisTable)
            q = q.join(gen_LabTable)
            q = q.filter(getattr(meas_AnalysisTable, 'labnumber') == ln)

            try:
                ai = int(ai)
            except ValueError:
                return

            q = q.filter(meas_AnalysisTable.aliquot == int(ai))
            if step:
                q = q.filter(meas_AnalysisTable.step == step)
            q = q.limit(1)
            try:
                return q.one()
            except NoResultFound:
                return

    def get_analysis_uuid(self, value):
    #         return self.get_analysis(value, key)
    # #        return meas_AnalysisTable, 'uuid'
        return self._retrieve_item(meas_AnalysisTable, value, key='uuid')

    def get_analysis_record(self, value):
        return self._retrieve_item(meas_AnalysisTable, value, key='id')

    def get_image(self, name):
        return self._retrieve_item(med_ImageTable, name, key='name')

    def get_analysis(self, value, key='lab_id'):
        return self._retrieve_item(meas_AnalysisTable, value, key=key)

    def get_analysis_type(self, value):
        return self._retrieve_item(gen_AnalysisTypeTable, value)

    def get_blank(self, value):
        return self._retrieve_item(proc_BlanksTable, value)

    def get_blanks_history(self, value):
        return self._retrieve_item(proc_BlanksHistoryTable, value)

    def get_background(self, value):
        return self._retrieve_item(proc_BackgroundsTable, value)

    def get_backgrounds_history(self, value):
        return self._retrieve_item(proc_BackgroundsHistoryTable, value, )

    def get_detector(self, value):
        return self._retrieve_item(gen_DetectorTable, value, )

    def get_detector_intercalibration(self, value):
        return self._retrieve_item(proc_DetectorIntercalibrationTable, value, )

    def get_detector_intercalibration_history(self, value):
        return self._retrieve_item(proc_DetectorIntercalibrationHistoryTable, value)

    def get_detector_intercalibrations_history(self, *args, **kw):
        return self.get_detector_intercalibration_history(*args, **kw)

    def get_experiment(self, value, key='name'):
        return self._retrieve_item(meas_ExperimentTable, value, key, )

    def get_extraction(self, value, key='id'):
        return self._retrieve_item(meas_ExtractionTable, value, key, )

    #    def get_extraction(self, value):
    #        return self._retrieve_item(meas_ExtractionTable, value, key='hash')

    def get_extraction_device(self, value):
        return self._retrieve_item(gen_ExtractionDeviceTable, value, )

    def get_figure(self, value, **kw):
        return self._retrieve_item(proc_FigureTable, value, **kw)

    def get_irradiation_chronology(self, value):
        return self._retrieve_item(irrad_ChronologyTable, value, )

    def get_load_holder(self, value):
        return self._retrieve_item(gen_LoadHolderTable, value, )

    def get_irradiation_holder(self, value):
        return self._retrieve_item(irrad_HolderTable, value, )

    def get_irradiation_production(self, value):
        return self._retrieve_item(irrad_ProductionTable, value, )

    def get_irradiation(self, value):
        return self._retrieve_item(irrad_IrradiationTable, value, )

    def get_irradiation_level_byid(self, lid):
        return self._retrieve_item(irrad_LevelTable, lid, key='id')

    def get_irradiation_level(self, irrad, level):
        with self.session_ctx() as s:
        #         with session(sess) as s:
        #         sess = self.get_session()
            q = s.query(irrad_LevelTable)
            q = q.join(irrad_IrradiationTable)
            q = q.filter(irrad_IrradiationTable.name == irrad)
            q = q.filter(irrad_LevelTable.name == level)
            try:
                return q.one()
            except Exception, _:
                pass

    def get_irradiation_position(self, irrad, level, pos):
        with self.session_ctx() as s:
        #         with session(sess) as s:
        #         sess = self.get_session()
            q = s.query(irrad_PositionTable)
            q = q.join(irrad_LevelTable)
            q = q.join(irrad_IrradiationTable)
            q = q.filter(irrad_IrradiationTable.name == irrad)
            q = q.filter(irrad_LevelTable.name == level)

            if isinstance(pos, (list, tuple)):
                q = q.filter(irrad_PositionTable.position.in_(pos))
                func = 'all'
            else:
                q = q.filter(irrad_PositionTable.position == pos)
                func = 'one'
            try:
                return getattr(q, func)()
            except Exception, _:
                pass

    def get_labnumber(self, labnum, **kw):
        return self._retrieve_item(gen_LabTable, labnum,
                                   key='identifier',
                                   **kw)

    #        if isinstance(labnum, str):
    #            labnum = convert_identifier(labnum)
    #
    #        try:
    #            labnum = int(labnum)
    #        except (ValueError, TypeError):
    #            pass
    #
    #        return self._retrieve_item(gen_LabTable, labnum, key='labnumber')

    def get_mass_spectrometer(self, value):
        return self._retrieve_item(gen_MassSpectrometerTable, value, )

    def get_material(self, value):
        return self._retrieve_item(gen_MaterialTable, value, )

    #    def get_measurement(self, value):
    #        return self._retrieve_item(meas_MeasurementTable, value, key='hash')

    def get_molecular_weight(self, value):
        return self._retrieve_item(gen_MolecularWeightTable, value)

    def get_user(self, value):
        return self._retrieve_item(gen_UserTable, value, )

    def get_project(self, value):
        return self._retrieve_item(gen_ProjectTable, value, )

    def get_script(self, value):
        return self._retrieve_item(meas_ScriptTable, value, key='hash', )

    def get_sample(self, value, project=None, material=None, **kw):
        if 'joins' not in kw:
            kw['joins'] = []
        if 'filters' not in kw:
            kw['filters'] = []

        if project:
            kw['joins'] += [gen_ProjectTable]
            kw['filters'] += [gen_ProjectTable.name == project]

        if material:
            kw['joins'] += [gen_MaterialTable]
            kw['filters'] += [gen_MaterialTable.name == material]

        return self._retrieve_item(gen_SampleTable, value, **kw)

    def get_flux_history(self, value):
        return self._retrieve_item(flux_HistoryTable, value)

    def get_flux_monitor(self, value, **kw):
        return self._retrieve_item(flux_MonitorTable, value, **kw)

    def get_tag(self, name):
        return self._retrieve_item(proc_TagTable, name)

    def get_sensitivity(self, sid):
        return self._retrieve_item(gen_SensitivityTable, sid, key='id')

    def get_interpreted_age_history(self, sid):
        return self._retrieve_item(proc_InterpretedAgeHistoryTable, sid, key='id')

    #===============================================================================
    # ##getters multiple
    #===============================================================================
    #     def get_analyses(self, **kw):
    #         return self._get_items(meas_AnalysisTable, globals(), **kw)

    '''
        new style using _retrieve_items, _get_items is deprecated. 
        rewrite functionality if required
    '''

    def get_irradiation_holders(self, **kw):
        return self._retrieve_items(irrad_HolderTable, **kw)

    def get_analyses(self, **kw):
        """
            kw: meas_Analysis attributes
                or callable predicate that accepts "meas_AnalysisTable" and "gen_LabTable"
        """
        with self.session_ctx() as sess:
            q = sess.query(meas_AnalysisTable)
            q = q.join(gen_LabTable)
            for k, v in kw.iteritems():
                if hasattr(v, '__call__'):
                    ff = v(meas_AnalysisTable, gen_LabTable)
                    q = q.filter(and_(*ff))

                else:
                    q = q.filter(getattr(meas_AnalysisTable, k) == v)

            q = q.order_by(gen_LabTable.identifier.asc())
            q = q.order_by(meas_AnalysisTable.aliquot.asc())
            q = q.order_by(meas_AnalysisTable.step.asc())
            q = q.order_by(meas_AnalysisTable.analysis_timestamp.desc())

            return q.all()

    def get_figures(self, project=None):
        if project:
            project = self.get_project(project)
            if project:
                return project.figures

        else:
            return self._retrieve_items(proc_FigureTable)

    def get_aliquots(self, **kw):
        return self._retrieve_items(meas_AnalysisTable, **kw)

    def get_detectors(self, **kw):
        return self._retrieve_items(gen_DetectorTable, **kw)

    def get_steps(self, **kw):
        return self._retrieve_items(meas_AnalysisTable, **kw)

    def get_materials(self, **kw):
        return self._retrieve_items(gen_MaterialTable, **kw)

    def get_recent_labnumbers(self, lpost, spectrometer=None):
        with self.session_ctx() as sess:
            q = sess.query(gen_LabTable)
            q = q.join(meas_AnalysisTable)

            if spectrometer:
                q = q.join(meas_MeasurementTable)
                q = q.join(gen_MassSpectrometerTable)
                q = q.filter(gen_MassSpectrometerTable.name == spectrometer.lower())

            q = q.filter(meas_AnalysisTable.analysis_timestamp >= lpost)
            q = q.order_by(meas_AnalysisTable.analysis_timestamp.asc())

            return self._query_all(q)

    def get_recent_samples(self, lpost, spectrometer=None):
        with self.session_ctx() as sess:
            q = sess.query(gen_SampleTable).join(gen_LabTable)
            q = q.join(meas_AnalysisTable)

            if spectrometer:
                q = q.join(meas_MeasurementTable)
                q = q.join(gen_MassSpectrometerTable)
                q = q.filter(gen_MassSpectrometerTable.name == spectrometer.lower())

            q = q.filter(meas_AnalysisTable.analysis_timestamp >= lpost)
            q = q.order_by(meas_AnalysisTable.analysis_timestamp.asc())

            return self._query_all(q)

    def get_samples(self, project=None, **kw):

        if project:
            f = []
            if 'filters' in kw:
                f = kw['filters']
            f.append(gen_ProjectTable.name == project)
            kw['filters'] = f

            j = []
            if 'joins' in kw:
                j = kw['joins']
            j.append(gen_ProjectTable)
            kw['joins'] = j

        return self._retrieve_items(gen_SampleTable, **kw)

    def get_users(self, **kw):
        return self._retrieve_items(gen_UserTable, **kw)

    def get_labnumbers(self, identifiers=None, **kw):
        if identifiers:
            f=gen_LabTable.identifier.in_(identifiers)
            if 'filters' in kw:
                kw['filters'].append(f)
            else:
                kw['filters']=[f]

        # print self.name, identifiers
        # with self.session_ctx() as sess:
        #     q=sess.query(gen_LabTable)
        #     # q=q.filter(gen_LabTable.identifier=='61551')
        #     return q.all()
        # print identifiers, kw, self.name
        return self._retrieve_items(gen_LabTable, **kw)

    def get_flux_monitors(self, **kw):
        return self._retrieve_items(flux_MonitorTable, **kw)

    def get_irradiations(self, names=None, order_func='desc', **kw):
        """
            if names is callable should take from of F(irradiationTable)
            returns list of filters
        """
        if names is not None:
            if hasattr(names, '__call__'):
                f = names(irrad_IrradiationTable)
            else:
                f = (irrad_IrradiationTable.name.in_(names),)
            kw['filters'] = f

            #        return self._retrieve_items(irrad_IrradiationTable, order=irrad_IrradiationTable.name, ** kw)
        return self._retrieve_items(irrad_IrradiationTable,
                                    order=getattr(irrad_IrradiationTable.name, order_func)(),
                                    **kw)

    def get_irradiation_productions(self, **kw):
        return self._retrieve_items(irrad_ProductionTable, **kw)

    def get_projects(self, **kw):
        return self._retrieve_items(gen_ProjectTable, **kw)

    def get_sensitivities(self, **kw):
        return self._retrieve_items(gen_SensitivityTable, **kw)

    def get_mass_spectrometers(self, **kw):
        return self._retrieve_items(gen_MassSpectrometerTable, **kw)

    def get_extraction_devices(self, **kw):
        return self._retrieve_items(gen_ExtractionDeviceTable, **kw)

    def get_analysis_types(self, **kw):
        return self._retrieve_items(gen_AnalysisTypeTable, **kw)

    def get_spectrometer_parameters(self, value):
        return self._retrieve_item(meas_SpectrometerParametersTable, value,
                                   key='hash', )

    def get_load_holders(self, **kw):
        return self._retrieve_items(gen_LoadHolderTable, **kw)

    def get_loads(self, **kw):
        return self._retrieve_items(loading_LoadTable, **kw)

    def get_molecular_weights(self, **kw):
        return self._retrieve_items(gen_MolecularWeightTable, **kw)

    def get_tags(self, **kw):
        return self._retrieve_items(proc_TagTable, **kw)

    def delete_tag(self, v):
        self._delete_item(v, name='tag')

    def delete_irradiation_position(self, p):
        with self.session_ctx():
            self._delete_item(p.labnumber)
            for fi in p.flux_histories:
                self._delete_item(fi.flux)
                self._delete_item(fi)
            self._delete_item(p)

    #===============================================================================
    # deleters
    #===============================================================================
    @delete_one
    def delete_user(self, name):
        return gen_UserTable

    @delete_one
    def delete_project(self, name):
        return gen_ProjectTable

    @delete_one
    def delete_material(self, name):
        return gen_MaterialTable

    @delete_one
    def delete_sample(self, name):
        return gen_SampleTable

    @delete_one
    def delete_labnumber(self, name):
        return gen_LabTable, 'labnumber'


    #===============================================================================
    # private
    #===============================================================================
    #    def _get_script(self, name, txt):
    #        getter = getattr(self, 'get_{}'.format(name))
    #        m = self._hash_factory()
    #        m.update(txt)
    #        return getter(m.hexdigest())

    def _make_hash(self, txt):
        if isinstance(txt, dict):
            txt = repr(frozenset(txt.items()))

        ha = self._hash_factory(txt)
        return ha.hexdigest()

    def _hash_factory(self, text):
        return hashlib.md5(text)



        #def _build_query_and(self, table, name, jtable, attr, q=None):
        #    '''
        #        joins table and jtable
        #        filters using an andclause
        #
        #        e.g.
        #        q=sess.query(Table).join(JTable).filter(and_(Table.name==name, JTable.name==attr.name))
        #
        #    '''
        #
        #    sess = self.get_session()
        #    andclause = tuple()
        #    if q is None:
        #        q = sess.query(table)
        #        andclause = (table.name == name,)
        #
        #    if attr:
        #        q = q.join(jtable)
        #        andclause += (jtable.name == attr.name,)
        #
        #    if len(andclause) > 1:
        #        q = q.filter(and_(*andclause))
        #
        #    elif len(andclause) == 1:
        #        q = q.filter(andclause[0])
        #
        #    return q


if __name__ == '__main__':
    from pychron.core.helpers.logger_setup import logging_setup

    logging_setup('ia')
    ia = IsotopeAdapter(

        #                        name='isotopedb_dev_migrate',
        #                        name='isotopedb_FC2',
        name='isotopedb_dev',
        username='root',
        password='Argon',
        host='localhost',
        kind='mysql'
        #                        name='/Users/ross/Sandbox/exprepo/root/isotopedb.sqlite',
        #                        name=paths.isotope_db,
        #                        kind='sqlite'
    )

    if ia.connect():
        dbs = IsotopeAnalysisSelector(db=ia,
                                      #                                      style='simple'
        )
        #        repo = Repository(root=paths.isotope_dir)
        #        repo = Repository(root='/Users/ross/Sandbox/importtest')
        #        repo = ZIPRepository(root='/Users/ross/Sandbox/importtest/archive004.zip')
        #        dbs.set_data_manager(kind='local',
        #                             repository=repo,
        #                             workspace_root=paths.default_workspace_dir
        #                             )
        #    dbs._execute_query()
        #        dbs.load_recent()
        dbs.load_last(n=100)

        dbs.configure_traits()
        #    ia.add_user(project=p, name='mosuer', commit=True)
        #    p = ia.get_project('Foo3')
        #    m = ia.get_material('sanidine')
        #    ia.add_sample(name='FC-7sdh2n', project=p, material=m, commit=True)
        #===========================================================================
        # test getting
        #===========================================================================
#    print ia.get_user('mosuer').id
#============= EOF =============================================
