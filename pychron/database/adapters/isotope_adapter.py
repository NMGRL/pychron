# ===============================================================================
# Copyright 2012 Jake Ross
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ===============================================================================

# ============= enthought library imports =======================

from traits.api import provides

# ============= standard library imports ========================
from datetime import datetime, timedelta
from cStringIO import StringIO
import hashlib
from sqlalchemy import Date, distinct
from sqlalchemy.sql.functions import count
from sqlalchemy.sql.expression import and_, func, not_, cast as sql_cast
from sqlalchemy.orm.exc import NoResultFound
# ============= local library imports  ==========================
from pychron.database.core.functions import delete_one
from pychron.database.core.database_adapter import DatabaseAdapter
from pychron.database.core.query import compile_query
from pychron.database.i_browser import IBrowser

# spec_
from pychron.database.orms.isotope.spec import spec_MassCalHistoryTable, spec_MassCalScanTable, spec_MFTableTable

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
    meas_ScriptTable, meas_MonitorTable, meas_GainHistoryTable, meas_GainTable

# proc_
from pychron.database.orms.isotope.proc import proc_DetectorIntercalibrationHistoryTable, \
    proc_DetectorIntercalibrationTable, proc_SelectedHistoriesTable, \
    proc_BlanksTable, proc_BackgroundsTable, proc_BlanksHistoryTable, proc_BackgroundsHistoryTable, \
    proc_IsotopeResultsTable, proc_FitHistoryTable, \
    proc_FitTable, proc_DetectorParamTable, proc_NotesTable, proc_FigureTable, proc_FigureAnalysisTable, \
    proc_FigurePrefTable, proc_TagTable, proc_ArArTable, proc_InterpretedAgeHistoryTable, proc_InterpretedAgeSetTable, \
    proc_InterpretedAgeGroupHistoryTable, proc_InterpretedAgeGroupSetTable, proc_FigureLabTable, \
    proc_SensitivityHistoryTable, proc_SensitivityTable, \
    proc_AnalysisGroupTable, proc_AnalysisGroupSetTable, proc_DataReductionTagTable, proc_DataReductionTagSetTable, \
    proc_BlanksSetValueTable, proc_ActionTable, proc_BlanksSetTable

from pychron.pychron_constants import ALPHAS, alpha_to_int, NULL_STR


def binfunc(ds, hours):
    p1 = ds[0][0]
    delta_seconds = hours * 3600
    td = timedelta(seconds=delta_seconds * 0.25)

    for i, di in enumerate(ds):
        i = max(0, i - 1)

        di = di[0]
        dd = ds[i][0]
        if (di - dd).total_seconds() > delta_seconds:
            yield p1 - td, dd + td
            p1 = di

    yield p1 - td, di + td


# class session(object):
# def __call__(self, f):
#         def wrapped_f(obj, *args, **kw):
#             with obj.session_ctx() as sess:
#                 kw['sess']=sess
#                 return f(obj, *args, **kw)
#
#         return wrapped_f


@provides(IBrowser)
class IsotopeAdapter(DatabaseAdapter):
    """
        new style adapter
        be careful with super methods you use they may deprecate

        using decorators is the new model
    """

    # selector_klass = IsotopeAnalysisSelector

    @property
    def selector_klass(self):
        from pychron.database.selectors.isotope_selector import IsotopeAnalysisSelector

        return IsotopeAnalysisSelector

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
        from pychron.database.interpreted_age import InterpretedAge

        dbln = self.get_labnumber(hi.identifier)
        sample = None
        irrad = None
        material = None
        lithology = None
        if dbln:
            if dbln.sample:
                lithology = dbln.sample.lithology
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
        if ia:
            if ia.age_kind == 'Plateau':
                n = len(filter(lambda x: x.plateau_step, ia.sets))
            else:
                n = len(ia.sets)

            it = InterpretedAge(create_date=hi.create_date,
                                id=hi.id,
                                age=ia.age,
                                age_err=ia.age_err,
                                display_age_units=ia.display_age_units or 'Ma',
                                kca=ia.kca or 0,
                                kca_err=ia.kca_err or 0,
                                mswd=ia.mswd,
                                age_kind=ia.age_kind,
                                kca_kind=ia.kca_kind,
                                identifier=hi.identifier,
                                sample=sample or '',
                                irradiation=irrad or '',
                                material=material or '',
                                lithology=lithology or '',
                                nanalyses=n,
                                name='{} - {}'.format(hi.create_date, ia.age_kind))

            return it

    # ===========================================================================
    # adders
    # ===========================================================================
    def add_data_reduction_tag(self, name, comment, user=None):
        if user:
            user = self.get_user(self.save_username)

        obj = proc_DataReductionTagTable(name=name, comment=comment, user=user)
        return self._add_item(obj)

    def add_data_reduction_tag_set(self, dbtag, an, sh_id):
        obj = proc_DataReductionTagSetTable()
        obj.tag = dbtag
        obj.analysis = an
        obj.selected_histories_id = sh_id

    def add_proc_action(self, msg, **kw):
        obj = proc_ActionTable(action=msg, **kw)
        return self._add_item(obj)

    def add_mftable(self, specname, blob):
        spec = self.get_mass_spectrometer(specname)
        if spec is None:
            self.warning('Invalid spectrometer: {}'.format(specname))

        obj = spec_MFTableTable(blob=blob, spectrometer=spec)
        self._add_item(obj)

    def add_analysis_group(self, name, **kw):
        obj = proc_AnalysisGroupTable(name=name, **kw)
        self._add_item(obj)
        return obj

    def add_analysis_group_set(self, group, analysis, **kw):
        obj = proc_AnalysisGroupSetTable(analysis_id=analysis.id, **kw)
        self._add_item(obj)

        if isinstance(group, (int, long)):
            obj.group_id = group
        else:
            group.analyses.append(obj)
        return obj

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

    def add_history(self, dbrecord, kind, **kw):
        func = getattr(self, 'add_{}_history'.format(kind))
        history = func(dbrecord, user=self.save_username, **kw)
        # history = db.add_blanks_history(dbrecord, user=db.save_username)

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
            # dbm.analysis_id = analysis.id
            #             analysis.monitors.append(dbm)
        self._add_item(dbm)
        return dbm

    def add_analysis_position(self, extraction, pos, **kw):
        try:
            pos = int(pos)
            dbpos = meas_PositionTable(position=pos, **kw)
            if extraction:
                dbpos.extraction_id = extraction.id
                # extraction.positions.append(dbpos)
            self._add_item(dbpos)
            return dbpos
        except (ValueError, TypeError), e:
            pass

    def add_note(self, analysis, note, **kw):
        analysis = self.get_analysis(analysis)
        obj = proc_NotesTable(note=note, user=self.save_username)
        if analysis:
            note.analysis = analysis
            # analysis.notes.append(obj)
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
        # return self._add_set('InterpretedAge', 'interpreted_age',
        #                     interpreted_age, analysis, **kw)

    def add_blanks_history(self, analysis, **kw):
        return self._add_history('Blanks', analysis, **kw)

    def add_blanks(self, history, **kw):
        return self._add_series_item('Blanks', 'blanks', history, **kw)

    def add_blanks_set(self, analysis, **kw):
        return self._add_set('Blanks', 'blank', analysis, **kw)

    def add_blank_set_value_table(self, v, e, blank, analysis):
        item = proc_BlanksSetValueTable(value=float(v), error=float(e))
        dbitem = self._add_item(item)
        dbitem.blank = blank
        if isinstance(analysis, (int, long)):
            dbitem.analysis_id = analysis
        else:
            dbitem.analysis = analysis

        return dbitem

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
        # obj.history_id = history.id

        self._add_item(obj)

        return obj

    def add_detector_intercalibration_history(self, analysis, **kw):
        return self._add_history('DetectorIntercalibration', analysis, **kw)

    def add_detector_intercalibration(self, history, detector, **kw):
        a = self._add_series_item('DetectorIntercalibration',
                                  'detector_intercalibrations', history, **kw)
        if a:
            detector = self.get_detector(detector)
            # if detector:
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
        # ex = self._get_script('extraction', script_blob)
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
            # fa.figure_id = figure.id

        analysis = self.get_analysis(analysis)
        if analysis:
            fa.analysis = analysis
            # fa.analysis_id = analysis.id

        self._add_item(fa)
        return fa

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
        # self._add_item(ir)
        return self._add_unique(ir, 'irradiation', name)
        # return ir

    def add_load_holder(self, name, **kw):
        lh = gen_LoadHolderTable(name=name, **kw)
        return self._add_unique(lh, 'load_holder', name, )

    def add_irradiation_holder(self, name, **kw):
        ih = irrad_HolderTable(name=name, **kw)
        return self._add_unique(ih, 'irradiation_holder', name, )

    def add_irradiation_production(self, **kw):
        ip = irrad_ProductionTable(**kw)
        self._add_item(ip)
        return ip

    def add_irradiation_position(self, pos, labnumber, irrad, level, **kw):
        if labnumber:
            labnumber = self.get_labnumber(labnumber)

        dbirrad = self.get_irradiation(irrad)
        if dbirrad:
            if isinstance(level, (str, unicode)):
                level = next((li for li in dbirrad.levels if li.name == level), None)

            if level:
                dbpos = next((di for di in level.positions if di.position == pos), None)
                if not dbpos:
                    dbpos = irrad_PositionTable(position=pos, **kw)

                    dbpos.level = level
                    self._add_item(dbpos)

                if labnumber:
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
                if holder is None:
                    holder = self.get_irradiation_holder('tube')

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
        analysis = self.get_analysis(analysis)
        det = self.get_detector(det)

        if isinstance(molweight, float):
            molweight = self.get_molecular_weight(molweight)
        else:
            molweight = self.get_molecular_weight_name(molweight)

        iso = meas_IsotopeTable(**kw)

        iso.molecular_weight = molweight
        iso.analysis = analysis
        iso.detector = det

        self._add_item(iso)
        return iso

    def add_isotope_result(self, isotope, history, **kw):
        r = proc_IsotopeResultsTable(**kw)
        r.isotope = isotope
        r.history = history

        self._add_item(r, )
        return r

    def add_measurement(self, analysis, analysis_type, mass_spec, **kw):
        meas = meas_MeasurementTable(**kw)

        self._add_item(meas)

        an = self.get_analysis(analysis)
        at = self.get_analysis_type(analysis_type)
        ms = self.get_mass_spectrometer(mass_spec)
        if an:
            an.measurement = meas

        meas.mass_spectrometer = ms
        meas.analysis_type = at

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

    def add_sample(self, name, project=None, material=None, **kw):
        with self.session_ctx() as sess:

            q = sess.query(gen_SampleTable)
            if project:
                project = self.get_project(project)
                q = q.filter(gen_SampleTable.project == project)

            if material:
                material = self.get_material(material)
                q = q.filter(gen_SampleTable.material == material)

            q = q.filter(gen_SampleTable.name == name)

            try:
                sample = q.one()
            except Exception, e:
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

        return sp

    def add_deflection(self, meas, det, value):
        sp = meas_SpectrometerDeflectionsTable(deflection=value)
        sp.measurement = meas
        det = self.get_detector(det)
        sp.detector = det

        return sp

    def add_labnumber(self, labnumber,
                      sample=None,
                      unique=True,
                      **kw):
        with self.session_ctx():
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

    def add_gain_history(self, ha, **kw):
        item = meas_GainHistoryTable(hash=ha, **kw)
        user = self.get_user(self.save_username)
        if user:
            item.user_id = user.id

        return self._add_item(item)

    def add_gain(self, d, v, hist):
        obj = meas_GainTable()
        detector = self.get_detector(d)
        if detector:
            obj.detector = detector
        obj.value = v
        obj.history = hist
        return self._add_item(obj)

    # ===========================================================================
    # getters
    # ===========================================================================
    def get_adjacent_analysis(self, timestamp, previous):
        with self.session_ctx() as sess:
            q = sess.query(meas_AnalysisTable)
            if previous:
                q = q.filter(meas_AnalysisTable.analysis_timestamp < timestamp)
                q = q.order_by(meas_AnalysisTable.analysis_timestamp.desc())
            else:
                q = q.filter(meas_AnalysisTable.analysis_timestamp > timestamp)
                q = q.order_by(meas_AnalysisTable.analysis_timestamp.asc())

            return self._query_first(q)

    def make_gains_hash(self, gains):
        h = hashlib.md5()

        for d, v in gains:
            h.update(d)
            h.update(str(v))

        return h.hexdigest()

    def get_gain_histories(self, lpost=None, hpost=None, **kw):
        if lpost:
            d = sql_cast(meas_GainHistoryTable.create_date, Date)
            kw = self._append_filters(d >= lpost)
        if hpost:
            d = sql_cast(meas_GainHistoryTable.create_date, Date)
            kw = self._append_filters(d <= hpost)

        return self._retrieve_items(meas_GainHistoryTable, **kw)

    def get_gain_history(self, v, **kw):
        # kw = self._append_filters(meas_GainHistoryTable.hash == v, kw)
        # order = meas_GainHistoryTable.create_date.desc()
        #
        # histories = self._retrieve_items(meas_GainHistoryTable,
        #                                  limit=1, order=order, **kw)
        # if histories:
        #     return histories[0]
        return self._retrieve_item(meas_GainHistoryTable, v, key='hash')

    def get_blanks(self, ms=None, limit=100):
        joins = (meas_AnalysisTable, gen_AnalysisTypeTable)
        filters = (gen_AnalysisTypeTable.name.like('blank%'),)
        if ms:
            joins.append(gen_MassSpectrometerTable)
            filters.append(gen_MassSpectrometerTable.name == ms.lower())

        return self._retrieve_items(meas_AnalysisTable,
                                    joins=joins, filters=filters,
                                    order=meas_AnalysisTable.analysis_timestamp.desc(),
                                    limit=limit)

    def get_session_blank_histories(self, s):
        with self.session_ctx() as sess:
            q = sess.query(proc_BlanksHistoryTable)
            q = q.filter(proc_BlanksHistoryTable.session == s)
            return self._query_all(q)

    def get_blanks_history(self, value, key='id'):
        return self._retrieve_item(proc_BlanksHistoryTable, value, key=key)

    def get_mftables(self, spec, **kw):
        return self._retrieve_items(spec_MFTableTable,
                                    joins=(gen_MassSpectrometerTable,),
                                    filters=(gen_MassSpectrometerTable.name == spec,),
                                    order=spec_MFTableTable.create_date.desc(),
                                    **kw)

    def get_mftable(self, value, key='id'):
        return self._retrieve_item(spec_MFTableTable, value, key=key)

    def get_interpreted_age_group_history(self, gid):
        return self._retrieve_item(proc_InterpretedAgeGroupHistoryTable,
                                   gid, key='id')


    def get_interpreted_age_groups(self, project):
        with self.session_ctx() as sess:
            # q = sess.query(proc_InterpretedAgeGroupHistoryTable)
            # q = q.join(gen_ProjectTable)

            # q = q.filter(gen_ProjectTable.name == project)
            # return self._query_all(q)
            return self._retrieve_items(proc_InterpretedAgeGroupHistoryTable,
                                        joins=(gen_ProjectTable,),
                                        filters=(gen_ProjectTable.name == project))

    def get_analyzed_positions(self, level):
        table = (irrad_PositionTable.position, func.count(meas_AnalysisTable.id))
        joins = (gen_LabTable, meas_AnalysisTable,
                 irrad_LevelTable, irrad_IrradiationTable, )
        #
        # table = (irrad_PositionTable.position,)
        # joins = (irrad_LevelTable, irrad_IrradiationTable)

        filters = (irrad_IrradiationTable.name == level.irradiation.name,
                   irrad_LevelTable.name == level.name)
        group_by = irrad_PositionTable.position

        return self._retrieve_items(table,
                                    joins=joins,
                                    filters=filters,
                                    group_by=group_by)

    def get_analysis_group(self, v, key='id', **kw):
        return self._retrieve_item(proc_AnalysisGroupTable, v, key, **kw)

    def get_analysis_groups(self, projects=None):
        if projects:
            joins = (proc_AnalysisGroupSetTable, meas_AnalysisTable, gen_LabTable, gen_SampleTable,
                     gen_ProjectTable)
            filters = (gen_ProjectTable.name.in_(projects),)
            order_bys = (proc_AnalysisGroupTable.create_date, proc_AnalysisGroupTable.last_modified)
            return self._retrieve_items(proc_AnalysisGroupTable,
                                        joins=joins,
                                        filters=filters, order=order_bys)

    def get_latest_interpreted_age_history(self, value, key='identifier'):
        with self.session_ctx() as sess:
            q = sess.query(proc_InterpretedAgeHistoryTable)

            attr = getattr(proc_InterpretedAgeHistoryTable, key)
            q = q.filter(attr.__eq__(value))
            q = q.order_by(proc_InterpretedAgeHistoryTable.create_date.desc())
            return self._query(q, 'first')

    def get_interpreted_age_histories(self, values, key='identifier'):
        with self.session_ctx() as sess:
            q = sess.query(proc_InterpretedAgeHistoryTable)

            attr = getattr(proc_InterpretedAgeHistoryTable, key)
            q = q.filter(attr.in_(values))
            q = q.order_by(proc_InterpretedAgeHistoryTable.create_date.desc())

            return self._query_all(q)

    def get_project_irradiation_labnumbers(self, project_names, irradiation, level,
                                           mass_spectrometers=None,
                                           analysis_types=None,
                                           filter_non_run=None,
                                           low_post=None,
                                           high_post=None):

        with self.session_ctx() as sess:
            q = self._simple_query(sess, gen_LabTable, irrad_PositionTable, irrad_LevelTable,
                                   irrad_IrradiationTable, gen_SampleTable, gen_ProjectTable)

            q = self._labnumber_join(q, project_names, mass_spectrometers,
                                     analysis_types, filter_non_run, low_post, high_post)

            q = q.filter(irrad_IrradiationTable.name == irradiation)

            if level:
                q = q.filter(irrad_LevelTable.name == level)

            q = self._labnumber_filter(q, project_names, mass_spectrometers,
                                       analysis_types, filter_non_run, low_post, high_post)
            self.debug(compile_query(q))
            return self._query_all(q)

    def get_project_labnumbers(self, project_names, filter_non_run, low_post=None, high_post=None,
                               analysis_types=None, mass_spectrometers=None):
        with self.session_ctx() as sess:
            q = self._simple_query(sess, gen_LabTable, gen_SampleTable, gen_ProjectTable)

            q = self._labnumber_join(q, project_names, mass_spectrometers,
                                     analysis_types, filter_non_run, low_post, high_post)

            q = self._labnumber_filter(q, project_names, mass_spectrometers,
                                       analysis_types, filter_non_run, low_post, high_post, cast_date=False)
            self.debug(compile_query(q))
            return self._query_all(q)

    def get_project_analysis_count(self, projects):
        if not hasattr(projects, '__iter__'):
            projects = (projects,)
        with self.session_ctx() as sess:
            q = self._analysis_query(sess, gen_SampleTable, gen_ProjectTable)
            q = q.filter(gen_ProjectTable.name.in_(projects))
            try:
                return int(q.count())
            except NoResultFound:
                pass

    def get_project_figures(self, projects):
        if not hasattr(projects, '__iter__'):
            projects = (projects,)
        return self._retrieve_items(proc_FigureTable,
                                    joins=(gen_ProjectTable,),
                                    filters=(gen_ProjectTable.name.in_(projects),))

    def get_project_date_bins(self, identifier, pname, hours=10):
        with self.session_ctx() as sess:
            l, h = self.get_project_date_range([pname])
            #get date range of this identifier in the projects time frame
            q = sess.query(meas_AnalysisTable.analysis_timestamp)
            q = q.join(gen_LabTable)
            q = q.filter(gen_LabTable.identifier == identifier)
            q = q.filter(and_(meas_AnalysisTable.analysis_timestamp >= l,
                              meas_AnalysisTable.analysis_timestamp <= h))
            l, h = self._get_date_range(q)

            q = sess.query(meas_AnalysisTable.analysis_timestamp)
            q = q.join(gen_LabTable, gen_SampleTable, gen_ProjectTable)
            q = q.filter(gen_ProjectTable.name == pname)
            q = q.filter(and_(meas_AnalysisTable.analysis_timestamp >= l,
                              meas_AnalysisTable.analysis_timestamp <= h))

            q = q.order_by(meas_AnalysisTable.analysis_timestamp.asc())
            ans = q.all()
            if len(ans):
                return binfunc(ans, hours)

    def get_project_date_range(self, projects):
        with self.session_ctx() as sess:
            q = sess.query(meas_AnalysisTable.analysis_timestamp)
            q = q.join(gen_LabTable, gen_SampleTable, gen_ProjectTable)
            q = q.filter(gen_ProjectTable.name.in_(projects))

            return self._get_date_range(q)

    def get_labnumber_figures(self, identifiers):
        if not hasattr(identifiers, '__iter__'):
            identifiers = (identifiers,)

        return self._retrieve_items(proc_FigureTable,
                                    joins=(proc_FigureLabTable, gen_LabTable),
                                    filters=(gen_LabTable.identifier.in_(identifiers),))

    def get_preceding(self, post, ms, atype='blank_unknown'):
        joins = (meas_MeasurementTable, gen_AnalysisTypeTable, gen_MassSpectrometerTable)
        filters = (gen_AnalysisTypeTable.name == atype,
                   gen_MassSpectrometerTable.name == ms,
                   meas_AnalysisTable.analysis_timestamp < post)

        return self._retrieve_items(meas_AnalysisTable,
                                    joins=joins,
                                    filters=filters,
                                    order=meas_AnalysisTable.analysis_timestamp.desc(),
                                    func='first')

    def get_date_range_analyses(self, start, end,
                                labnumber=None,
                                atype=None,
                                spectrometer=None,
                                extract_device=None,
                                projects=None,
                                limit=None,
                                exclude_uuids=None,
                                ordering='desc'):

        with self.session_ctx() as sess:
            q = self._simple_query(sess, meas_AnalysisTable, meas_MeasurementTable)
            if atype:
                q = q.join(gen_AnalysisTypeTable)
            if labnumber:
                q = q.join(gen_LabTable)
            if spectrometer:
                q = q.join(gen_MassSpectrometerTable)
            if extract_device:
                q = q.join(meas_ExtractionTable, gen_ExtractionDeviceTable)
            if projects:
                q = q.join(gen_LabTable, gen_SampleTable, gen_ProjectTable)

            if atype:
                if isinstance(atype, (list, tuple)):
                    q = q.filter(gen_AnalysisTypeTable.name.in_(atype))
                else:
                    q = q.filter(gen_AnalysisTypeTable.name == atype)
            if labnumber:
                q = q.filter(gen_LabTable.identifier == labnumber)

            if spectrometer:
                if hasattr(spectrometer, '__iter__'):
                    q = q.filter(gen_MassSpectrometerTable.name.in_(spectrometer))
                else:
                    q = q.filter(gen_MassSpectrometerTable.name == spectrometer)

            if extract_device:
                q = q.filter(gen_ExtractionDeviceTable.name == extract_device)
            if projects:
                q = q.filter(gen_ProjectTable.name.in_(projects))

            q = q.filter(and_(meas_AnalysisTable.analysis_timestamp <= end,
                              meas_AnalysisTable.analysis_timestamp >= start))
            if exclude_uuids:
                q = q.filter(not_(meas_AnalysisTable.uuid.in_(exclude_uuids)))

            q = q.order_by(getattr(meas_AnalysisTable.analysis_timestamp, ordering)())
            if limit:
                q = q.limit(limit)

            return self._query_all(q)

    def get_analysis_mass_spectrometers(self, lns):
        """
            lns: list of labnumbers/identifiers
            return: list of str

            returns all mass spectrometer used to analyze labnumbers in lns
        """
        items = self._retrieve_items(distinct(gen_MassSpectrometerTable.name),
                                     joins=(meas_MeasurementTable, meas_AnalysisTable, gen_LabTable),
                                     filters=(gen_LabTable.identifier.in_(lns),))
        return [r for r, in items]

    def get_analysis_date_ranges(self, lns, hours):
        """
            lns: list of labnumbers/identifiers
        """

        with self.session_ctx() as sess:
            q = self._analysis_query(sess, attr='analysis_timestamp')

            q = q.filter(gen_LabTable.identifier.in_(lns))
            q = q.order_by(meas_AnalysisTable.analysis_timestamp.asc())
            ts = self._query_all(q)

            return list(binfunc(ts, hours))

    def get_min_max_analysis_timestamp(self, lns=None, projects=None, delta=0):
        """
            lns: list of labnumbers/identifiers
            return: datetime, datetime

            get the min and max analysis_timestamps for all analyses with labnumbers in lns
        """

        with self.session_ctx() as sess:
            q = self._analysis_query(sess, attr='analysis_timestamp')
            if lns:
                q = q.filter(gen_LabTable.identifier.in_(lns))

            elif projects:
                q = q.join(gen_SampleTable, gen_ProjectTable)
                q = q.filter(gen_ProjectTable.name.in_(projects))

            return self._get_date_range(q, hours=delta)

            # hpost = q.order_by(meas_AnalysisTable.analysis_timestamp.desc()).first()
            # lpost = q.order_by(meas_AnalysisTable.analysis_timestamp.asc()).first()
            # td = timedelta(hours=delta)
            # return lpost[0] - td, hpost[0] + td

    def get_labnumber_mass_spectrometers(self, lns):
        """
            return all the mass spectrometers use to measure these labnumbers analyses

            returns (str, str,...)
        """
        with self.session_ctx() as sess:
            q = self._analysis_query(sess,
                                     meas_MeasurementTable, meas_AnalysisTable,
                                     before=True,
                                     cols=(distinct(gen_MassSpectrometerTable.name),))

            q = q.filter(gen_LabTable.identifier.in_(lns))
            return [di[0] for di in q.all()]

    def get_labnumber_analyses(self, lns, low_post=None, high_post=None,
                               omit_key=None, exclude_uuids=None, mass_spectrometers=None, **kw):
        """
            get analyses that have labnunmbers in lns.
            low_post and high_post used to filter a date range.
            posts are inclusive

            returns (list, int)
            list: list of analyses
            int: number of analyses

        """

        with self.session_ctx() as sess:
            q = self._analysis_query(sess)
            if mass_spectrometers:
                q = q.join(meas_MeasurementTable, gen_MassSpectrometerTable)

            if omit_key:
                q = q.join(proc_TagTable)

            if hasattr(lns, '__iter__'):
                q = q.filter(gen_LabTable.identifier.in_(lns))
            else:
                q = q.filter(gen_LabTable.identifier == lns)

            if low_post:
                q = q.filter(self._get_post_filter(low_post, '__ge__'))

            if high_post:
                q = q.filter(self._get_post_filter(high_post, '__le__'))

            if omit_key:
                q = q.filter(not_(getattr(proc_TagTable, omit_key)))

            if exclude_uuids:
                q = q.filter(not_(meas_AnalysisTable.uuid.in_(exclude_uuids)))

            if mass_spectrometers:
                q = q.filter(gen_MassSpectrometerTable.name.in_(mass_spectrometers))

            return self._get_paginated_analyses(q, **kw)

    def get_sample_analyses(self, samples, projects, **kw):
        if not isinstance(samples, (list, tuple)):
            samples = (samples,)

        with self.session_ctx() as sess:
            q = self._analysis_query(sess, gen_SampleTable, gen_ProjectTable)
            q = q.filter(gen_SampleTable.name.in_(samples))
            q = q.filter(gen_ProjectTable.name.in_(projects))

            return self._get_paginated_analyses(q, **kw)

    def get_analyses_date_range(self, mi, ma,
                                limit=None,
                                analysis_type=None,
                                mass_spectrometers=None,
                                extract_device=None,
                                project=None,
                                exclude_invalid=True):
        ed = extract_device
        ms = mass_spectrometers
        at = analysis_type
        pr = project
        with self.session_ctx() as sess:
            q = self._analysis_query(sess, meas_MeasurementTable)
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
                if hasattr(ms, '__iter__'):
                    q = q.filter(gen_MassSpectrometerTable.name.in_(ms))
                else:
                    q = q.filter(gen_MassSpectrometerTable.name == ms)
            if ed:
                q = q.filter(gen_ExtractionDeviceTable.name == ed)
            if at:
                q = q.filter(gen_AnalysisTypeTable.name == at)
            if pr:
                q = q.filter(gen_ProjectTable.name == pr)
            if mi:
                q = q.filter(self._get_post_filter(mi, '__ge__', cast=False))
            if ma:
                q = q.filter(self._get_post_filter(ma, '__le__', cast=False))

            if exclude_invalid:
                q = q.filter(meas_AnalysisTable.tag != 'invalid')

            q = q.order_by(meas_AnalysisTable.analysis_timestamp.asc())
            if limit:
                q = q.limit(limit)

            return self._query_all(q)

    # ===========================================================================
    # getters single
    # ===========================================================================
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

    def get_arar(self, k):
        return self._retrieve_item(proc_ArArTable, k, key='hash')

    def get_last_labnumbers(self, sample=None, limit=1000, excludes=None):
        with self.session_ctx() as s:
            #         sess = self.get_session()
            q = s.query(gen_LabTable.identifier)
            if sample:
                q = q.join(gen_SampleTable)
                q = q.filter(gen_SampleTable.name == sample)
                if excludes:
                    q = q.filter(not_(gen_SampleTable.name.in_(excludes)))
            elif excludes:
                q = q.join(gen_SampleTable)
                q = q.filter(not_(gen_SampleTable.name.in_(excludes)))

            q = q.order_by(func.abs(gen_LabTable.identifier).desc())
            q = q.limit(limit)
            return self._query_all(q)
            # try:
            #     ()
            # except NoResultFound, e:
            #     self.debug('get last labnumber {}'.format(e))
            #     return
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

    def get_greatest_identifier(self, **kw):
        with self.session_ctx() as sess:
            q = sess.query(gen_LabTable.identifier)
            q = q.order_by(gen_LabTable.identifier.desc())
            ret = self._query_first(q)
            return int(ret[0]) if ret else 0

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
                    return ALPHAS.index(step) if step else -1

    def get_last_analysis(self, ln=None, aliquot=None, spectrometer=None,
                          hours_limit=None,
                          analysis_type=None):
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

            if analysis_type:
                if not spectrometer:
                    q = q.join(meas_MeasurementTable)
                q = q.join(gen_AnalysisTypeTable)

            if spectrometer:
                q = q.filter(gen_MassSpectrometerTable.name == spectrometer)

            if ln:
                q = q.filter(meas_AnalysisTable.labnumber == ln)
                if aliquot:
                    q = q.filter(meas_AnalysisTable.aliquot == aliquot)

            if analysis_type:
                q = q.filter(gen_AnalysisTypeTable.name == analysis_type)

            if hours_limit:
                lpost = datetime.now() - timedelta(hours=hours_limit)
                q = q.filter(meas_AnalysisTable.analysis_timestamp >= lpost)

            q = q.order_by(meas_AnalysisTable.analysis_timestamp.desc())
            q = q.limit(1)
            try:
                r = q.one()
                self.debug('got last analysis {}-{}'.format(r.labnumber.identifier, r.aliquot))
                return r
            except NoResultFound, e:
                if ln:
                    name = ln.identifier
                elif spectrometer:
                    name = spectrometer

                if name:
                    self.debug('no analyses for {}'.format(name))
                else:
                    self.debug('no analyses for get_last_analysis')

                return 0

    def get_unique_analysis(self, ln, ai, step=None):
        #         sess = self.get_session()
        with self.session_ctx() as sess:
            dbln = self.get_labnumber(ln)
            if not dbln:
                self.debug('get_unique_analysis, no labnumber {}'.format(ln))
                return
            q = self._analysis_query(sess)
            q = q.filter(meas_AnalysisTable.labnumber == dbln)

            try:
                ai = int(ai)
            except ValueError, e:
                self.debug('get_unique_analysis aliquot={}.  {}'.format(ai, e))
                return

            q = q.filter(meas_AnalysisTable.aliquot == int(ai))
            if step:
                if not isinstance(step, int):
                    step = alpha_to_int(step)

                q = q.filter(meas_AnalysisTable.increment == step)

            # q = q.limit(1)
            try:
                return q.one()
            except NoResultFound:
                return

    def get_analyses_uuid(self, uuids, attr=None, record_only=False, analysis_only=False):
        with self.session_ctx() as sess:

            if analysis_only or attr:
                if attr is None:
                    attr = meas_AnalysisTable
                else:
                    attr = getattr(meas_AnalysisTable, attr)

                q = sess.query(attr)
            elif record_only:
                q = sess.query(meas_AnalysisTable)
            else:
                q = sess.query(meas_AnalysisTable,
                               gen_LabTable,
                               meas_IsotopeTable,
                               gen_SampleTable.name,
                               gen_ProjectTable.name,
                               gen_MaterialTable.name)
                q = q.join(meas_IsotopeTable)
                q = q.join(gen_LabTable)
                q = q.join(gen_SampleTable, gen_ProjectTable, gen_MaterialTable)

            q = q.filter(meas_AnalysisTable.uuid.in_(uuids))
            q = q.order_by(meas_AnalysisTable.analysis_timestamp.asc())

            return self._query_all(q)

    def get_analysis_isotopes(self, uuid):
        """
            this function is extremely slow and should not be used
        """
        with self.session_ctx() as sess:
            q = sess.query(meas_AnalysisTable, meas_IsotopeTable, gen_MolecularWeightTable)
            q = q.join(meas_IsotopeTable)
            q = q.join(gen_MolecularWeightTable)
            q = q.filter(meas_AnalysisTable.uuid == uuid)
            print compile_query(q)
            return self._query_all(q)

    def get_analysis_isotope(self, uuid, iso, kind):
        """
            this function is extremely slow and should not be used
        """
        with self.session_ctx() as sess:
            q = sess.query(meas_IsotopeTable)
            q = q.join(meas_AnalysisTable)
            q = q.join(gen_MolecularWeightTable)
            q = q.filter(meas_IsotopeTable.kind == kind)
            q = q.filter(gen_MolecularWeightTable.name == iso)
            q = q.filter(meas_AnalysisTable.uuid == uuid)
            print compile_query(q)
            try:
                return q.first()
            except NoResultFound:
                return []

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

    def get_blanks_set(self, value, key='set_id'):
        return self._retrieve_item(proc_BlanksSetTable, value, key=key)

    def retrieve_blank(self, kind, ms, ed, last):
        with self.session_ctx() as sess:
            q = sess.query(meas_AnalysisTable)
            q = q.join(meas_MeasurementTable, gen_AnalysisTypeTable)

            if last:
                q = q.filter(gen_AnalysisTypeTable.name == 'blank_{}'.format(kind))
            else:
                q = q.filter(gen_AnalysisTypeTable.name.startswith('blank'))

            if ms:
                q = q.join(gen_MassSpectrometerTable)
                q = q.filter(gen_MassSpectrometerTable.name == ms.lower())
            if ed and not ed in ('Extract Device', NULL_STR) and kind == 'unknown':
                q = q.join(meas_ExtractionTable, gen_ExtractionDeviceTable)
                q = q.filter(gen_ExtractionDeviceTable.name == ed)

            q = q.order_by(meas_AnalysisTable.analysis_timestamp.desc())
            return self._query_one(q)

    def get_blank(self, value, key='id'):
        return self._retrieve_item(proc_BlanksTable, value, key=key)

    def get_blanks_set(self, value, key='set_id'):
        return self._retrieve_item(proc_BlanksSetTable, value, key=key)

    def retrieve_blank(self, kind, ms, ed, last):
        with self.session_ctx() as sess:
            q = sess.query(meas_AnalysisTable)
            q = q.join(meas_MeasurementTable, gen_AnalysisTypeTable)

            if last:
                q = q.filter(gen_AnalysisTypeTable.name == 'blank_{}'.format(kind))
            else:
                q = q.filter(gen_AnalysisTypeTable.name.startswith('blank'))

            if ms:
                q = q.join(gen_MassSpectrometerTable)
                q = q.filter(gen_MassSpectrometerTable.name == ms.lower())
            if ed and not ed in ('Extract Device', NULL_STR) and kind == 'unknown':
                q = q.join(meas_ExtractionTable, gen_ExtractionDeviceTable)
                q = q.filter(gen_ExtractionDeviceTable.name == ed)

            q = q.order_by(meas_AnalysisTable.analysis_timestamp.desc())
            return self._query_one(q)

    def get_blank(self, value, key='id'):
        return self._retrieve_item(proc_BlanksTable, value, key=key)

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
        return self._retrieve_item(irrad_IrradiationTable, value)

    def get_irradiation_level_byid(self, lid):
        return self._retrieve_item(irrad_LevelTable, lid, key='id')

    def get_irradiation_level(self, irrad, level, mass_spectrometers=None):
        return self._retrieve_items(irrad_LevelTable,
                                    joins=(irrad_IrradiationTable,),
                                    filters=(irrad_IrradiationTable.name == irrad,
                                             irrad_LevelTable.name == level),
                                    func='one')
        # with self.session_ctx() as s:
        #     #         with session(sess) as s:
        #     #         sess = self.get_session()
        #     q = s.query(irrad_LevelTable)
        #     q = q.join(irrad_IrradiationTable)
        #     q = q.filter(irrad_IrradiationTable.name == irrad)
        #     q = q.filter(irrad_LevelTable.name == level)
        #     try:
        #         return q.one()

    #     except Exception, _:
    #         pass

    def get_irradiation_position(self, irrad, level, pos):
        with self.session_ctx() as sess:
            print irrad, level, pos
            q = sess.query(irrad_PositionTable)
            q = self._irrad_level(q, irrad, level)

            if isinstance(pos, (list, tuple)):
                q = q.filter(irrad_PositionTable.position.in_(pos))
                func = 'all'
            else:
                q = q.filter(irrad_PositionTable.position == pos)
                func = 'one'
            try:
                return getattr(q, func)()
            except Exception, e:
                pass

    def get_irradiation_labnumbers(self, irrad, level, low_post=None,
                                   high_post=None,
                                   mass_spectrometers=None,
                                   analysis_types=None, filter_non_run=False):
        with self.session_ctx() as sess:
            q = sess.query(gen_LabTable)
            q = q.join(irrad_PositionTable)
            q = q.join(irrad_LevelTable)
            q = q.join(irrad_IrradiationTable)
            q = self._labnumber_join(q, None, mass_spectrometers, analysis_types,
                                     filter_non_run, low_post, high_post)
            # if filter_non_run or low_post or high_post:
            #     q = q.join(meas_AnalysisTable)
            #     if analysis_types:
            #         q = q.join(meas_MeasurementTable, gen_AnalysisTypeTable)
            # elif analysis_types:
            #     q = q.join(meas_AnalysisTable, meas_MeasurementTable, gen_AnalysisTypeTable)
            #
            # q = self._irrad_level(q, irrad, level)
            # if analysis_types:
            #     q = q.filter(gen_AnalysisTypeTable.name.in_(analysis_types))
            #
            # if filter_non_run:
            #     q = q.group_by(gen_LabTable.id)
            #     q = q.having(count(meas_AnalysisTable.id) > 0)
            q = self._labnumber_filter(q, None, mass_spectrometers, analysis_types,
                                       filter_non_run, low_post, high_post)

            q = q.filter(irrad_IrradiationTable.name == irrad)
            if level:
                q = q.filter(irrad_LevelTable.name == level)
            self.debug(compile_query(q))
            return self._query_all(q)

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

    def get_molecular_weight_name(self, name):
        return self._retrieve_item(gen_MolecularWeightTable, name, key='name')

    def get_user(self, value):
        return self._retrieve_item(gen_UserTable, value, )

    def get_project(self, value):
        return self._retrieve_item(gen_ProjectTable, value, )

    def get_script(self, value):
        return self._retrieve_item(meas_ScriptTable, value, key='hash', )

    def get_sample(self, value, project=None, material=None, **kw):
        if project:
            kw = self._append_joins(gen_ProjectTable, kw)
            kw = self._append_filters(gen_ProjectTable.name == project, kw)

        if material:
            kw = self._append_joins(gen_MaterialTable, kw)
            kw = self._append_filters(gen_MaterialTable.name == material, kw)

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

    # ===============================================================================
    # ##getters multiple
    # ===============================================================================
    #     def get_analyses(self, **kw):
    #         return self._get_items(meas_AnalysisTable, globals(), **kw)

    '''
    new style using _retrieve_items, _get_items is deprecated.
    rewrite functionality if required
'''

    def get_data_reduction_tags(self, uuids=None):
        with self.session_ctx() as sess:
            q = sess.query(proc_DataReductionTagTable)
            if uuids:
                q = q.join(proc_DataReductionTagSetTable)
                q = q.join(meas_AnalysisTable)
                q = q.filter(meas_AnalysisTable.uuid.in_(uuids))

            q = q.order_by(proc_DataReductionTagTable.create_date.desc())
            return q.all()


    def get_irradiation_holders(self, **kw):
        return self._retrieve_items(irrad_HolderTable, **kw)

    def get_analyses(self, limit=None, **kw):
        """
        kw: meas_Analysis attributes
            or callable predicate that accepts "meas_AnalysisTable" and "gen_LabTable"
    """
        with self.session_ctx() as sess:
            q = self._analysis_query(sess)
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
            if limit:
                q = q.limit(limit)
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

    def get_material_names(self, **kw):
        ms = self._retrieve_items(gen_MaterialTable.name, **kw)
        return [mi[0] for mi in ms]

    def get_years_active(self):
        with self.session_ctx() as sess:
            q = sess.query(distinct(func.year(meas_AnalysisTable.analysis_timestamp)))
            q = q.order_by(meas_AnalysisTable.analysis_timestamp.desc())
            return [i[0] for i in self._query_all(q)]

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

            q = q.filter(self._get_post_filter(meas_AnalysisTable.analysis_timestamp, '__ge__', lpost))
            q = q.order_by(meas_AnalysisTable.analysis_timestamp.asc())

            return self._query_all(q)

    def get_samples(self, project=None, **kw):
        if project:
            if hasattr(project, '__iter__'):
                kw = self._append_filters(gen_ProjectTable.name.in_(project), kw)
            else:
                kw = self._append_filters(gen_ProjectTable.name == project, kw)
            kw = self._append_joins(gen_ProjectTable, kw)
        return self._retrieve_items(gen_SampleTable, **kw)

    def get_users(self, **kw):
        return self._retrieve_items(gen_UserTable, **kw)

    def get_usernames(self):
        return [u.name for u in self.get_users(order=gen_UserTable.name.asc())]

    def get_labnumbers_startswith(self, partial_id, mass_spectrometers=None, filter_non_run=True, **kw):
        f = gen_LabTable.identifier.like('{}%'.format(partial_id))
        kw = self._append_filters(f, kw)
        if mass_spectrometers or filter_non_run:
            kw = self._append_joins(meas_AnalysisTable, kw)

        if mass_spectrometers:
            kw = self._append_joins([meas_MeasurementTable, gen_MassSpectrometerTable], kw)
            kw = self._append_filters(gen_MassSpectrometerTable.name.in_(mass_spectrometers), kw)

        if filter_non_run:
            def func(q):
                q = q.group_by(gen_LabTable.id)
                q = q.having(count(meas_AnalysisTable.id) > 0)
                return q

                kw['query_hook'] = func

        return self._retrieve_items(gen_LabTable, verbose_query=True, **kw)

    def get_labnumbers(self, identifiers=None, low_post=None, high_post=None,
                       mass_spectrometers=None,
                       filter_non_run=False,
                       projects = None, **kw):

        if identifiers is not None:
            f = gen_LabTable.identifier.in_(identifiers)
            kw = self._append_filters(f, kw)

        if low_post or high_post:
            kw = self._append_joins(meas_AnalysisTable, kw)
            # joins=kw.get('joins',[])
            # joins.append(meas_AnalysisTable)
            # kw[joins]=joins

        if low_post:
            f = self._get_post_filter(low_post, '__ge__')
            kw = self._append_filters(f, kw)

        if high_post:
            f = self._get_post_filter(high_post, '__le__')
            kw = self._append_filters(f, kw)

        if filter_non_run or mass_spectrometers:
            kw = self._append_joins(meas_AnalysisTable, kw)

            if mass_spectrometers:
                kw = self._append_filters(gen_MassSpectrometerTable.name.in_(mass_spectrometers), kw)

            if filter_non_run:
                def func(q):
                    q = q.group_by(gen_LabTable.id)
                    q = q.having(count(meas_AnalysisTable.id) > 0)
                    return q

                kw['query_hook'] = func

        if projects:
            kw = self._append_joins((gen_SampleTable,gen_ProjectTable), kw)
            kw = self._append_filters(gen_ProjectTable.name.in_(projects), kw)

        return self._retrieve_items(gen_LabTable, verbose_query=True, **kw)

    def get_flux_monitors(self, **kw):
        return self._retrieve_items(flux_MonitorTable, **kw)

    def get_labnumbers_join_analysis(self, **kw):
        joins = kw['joins']

        if not joins:
            joins.append(meas_AnalysisTable)
        elif irrad_IrradiationTable in joins:
            joins.extend([j for j in [irrad_LevelTable, irrad_PositionTable, meas_AnalysisTable] if not j in joins])

        return self.get_labnumbers(
            order=gen_LabTable.identifier.desc(),
            distinct_=gen_LabTable.identifier,
            **kw)

    def get_irradiations_join_analysis(self, order_func='desc', **kw):
        # joins=kw.get('joins') or []
        # print joins
        # # joins.append(meas_AnalysisTable)
        # joins.insert(0, meas_AnalysisTable)
        # joins.reverse()
        kw['joins'] = [irrad_LevelTable, irrad_PositionTable, gen_LabTable, meas_AnalysisTable]

        return self._retrieve_items(irrad_IrradiationTable,
                                    order=getattr(irrad_IrradiationTable.name, order_func)(),
                                    distinct_=irrad_IrradiationTable.name,
                                    **kw)

    def get_irradiations(self, names=None, order_func='desc',
                         project_names=None,
                         mass_spectrometers=None, **kw):
        """
            if names is callable should take from of F(irradiationTable)
            returns list of filters
        """
        if names is not None:
            if hasattr(names, '__call__'):
                f = names(irrad_IrradiationTable)
            else:
                f = (irrad_IrradiationTable.name.in_(names),)
            kw = self._append_filters(f, kw)
            # kw['filters'] = f

        if project_names:
            # fs = kw.get('filters', [])
            # fs.append(gen_ProjectTable.name.in_(project_names))
            # kw['filters'] = fs
            kw = self._append_filters(gen_ProjectTable.name.in_(project_names), kw)
            kw = self._append_joins([irrad_LevelTable, irrad_PositionTable,
                                     gen_LabTable, gen_SampleTable, gen_ProjectTable], kw)
            # js = kw.get('joins', [])
            # js.extend()
            # kw['joins'] = js
            #        return self._retrieve_items(irrad_IrradiationTable, order=irrad_IrradiationTable.name, ** kw)

        if mass_spectrometers:
            kw = self._append_filters(gen_MassSpectrometerTable.name.in_(mass_spectrometers), kw)
            kw = self._append_joins([irrad_LevelTable, irrad_PositionTable,
                                     gen_LabTable, meas_AnalysisTable, meas_MeasurementTable,
                                     gen_MassSpectrometerTable], kw)

        return self._retrieve_items(irrad_IrradiationTable,
                                    order=getattr(irrad_IrradiationTable.name, order_func)(),
                                    **kw)

    def get_irradiation_productions(self, **kw):
        return self._retrieve_items(irrad_ProductionTable, **kw)

    def get_projects(self, irradiation=None, level=None, mass_spectrometers=None, **kw):
        if irradiation or mass_spectrometers:
            with self.session_ctx() as sess:
                if irradiation:
                    q = self._simple_query(sess, gen_ProjectTable, gen_SampleTable, gen_LabTable, irrad_PositionTable)
                    q = self._irrad_level(q, irradiation, level)
                elif mass_spectrometers:
                    q = self._simple_query(sess, gen_ProjectTable, gen_SampleTable, gen_LabTable,
                                           meas_AnalysisTable, meas_MeasurementTable, gen_MassSpectrometerTable)
                    q = q.filter(gen_MassSpectrometerTable.name.in_(mass_spectrometers))
                return self._query_all(q)
        else:
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

    def get_latest_load(self):
        return self._retrieve_first(loading_LoadTable,
                                    order_by=loading_LoadTable.create_date.desc())

    def get_loads(self, names=None, exclude_archived=True, **kw):
        if not kw.get('order'):
            kw['order'] = loading_LoadTable.create_date.desc()

        if exclude_archived:
            kw = self._append_filters(not_(loading_LoadTable.archived), kw)

        if names:
            kw = self._append_filters(loading_LoadTable.name.in_(names), kw)

        return self._retrieve_items(loading_LoadTable, **kw)

    def get_molecular_weights(self, **kw):
        return self._retrieve_items(gen_MolecularWeightTable, **kw)

    def get_molecular_weight_names(self, **kw):
        return self._retrieve_items(gen_MolecularWeightTable.name, **kw)

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

    def delete_analysis_group(self, id):
        with self.session_ctx():
            g = self.get_analysis_group(id)
            if g:
                self._delete_item(g)

    # ===============================================================================
    # deleters
    # ===============================================================================
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

    # ===============================================================================
    # private
    # ===============================================================================
    def _get_post_filter(self, post, comp, cast=True):
        t = meas_AnalysisTable.analysis_timestamp
        if cast and not isinstance(post, datetime):
            t = sql_cast(t, Date)

        return getattr(t, comp)(post)

    def _irrad_level(self, q, irrad, level):
        q = q.join(irrad_LevelTable)
        q = q.join(irrad_IrradiationTable)
        q = q.filter(irrad_IrradiationTable.name == irrad)
        if level:
            q = q.filter(irrad_LevelTable.name == level)
        return q

    def _analysis_query(self, sess, *args, **kw):
        """
            before: join args before (true) or after(false) gen_labtable
        """
        attr = kw.get('attr', None)
        cols = kw.get('cols', None)
        before = kw.get('before', False)

        if attr and hasattr(meas_AnalysisTable, attr):
            q = sess.query(getattr(meas_AnalysisTable, attr))
        elif cols:
            q = sess.query(*cols)
        else:
            q = sess.query(meas_AnalysisTable)

        if before:
            q = q.join(*args)
            q = q.join(gen_LabTable)
        else:
            q = q.join(gen_LabTable)
            q = q.join(*args)

        return q

    def _labnumber_join(self, q, project_names, mass_spectrometers,
                        analysis_types, filter_non_run, low_post, high_post):

        if filter_non_run or low_post or high_post or analysis_types or mass_spectrometers:
            q = q.join(meas_AnalysisTable)

        if mass_spectrometers or analysis_types:
            q = q.join(meas_MeasurementTable)

        if mass_spectrometers:
            q = q.join(gen_MassSpectrometerTable)

        if analysis_types:
            if project_names:
                project_names.append('references')
            q = q.join(gen_AnalysisTypeTable)

        return q

    def _labnumber_filter(self, q, project_names, mass_spectrometers,
                          analysis_types, filter_non_run, low_post, high_post, cast_date=True):
        if low_post:
            # q = q.filter(cast(meas_AnalysisTable.analysis_timestamp, Date) >= low_post)
            q = q.filter(self._get_post_filter(low_post, '__ge__', cast=cast_date))
        if high_post:
            # q = q.filter(cast(meas_AnalysisTable.analysis_timestamp, Date) <= high_post)
            q = q.filter(self._get_post_filter(high_post, '__le__', cast=cast_date))

        if analysis_types:
            f = gen_AnalysisTypeTable.name.in_(analysis_types)

            # fix for issue #452
            # if 'blank' in analysis_types:
            #     f = f | gen_AnalysisTypeTable.name.like('blank%')

            q = q.filter(f)

        if mass_spectrometers:
            q = q.filter(gen_MassSpectrometerTable.name.in_(mass_spectrometers))
        if project_names:
            q = q.filter(gen_ProjectTable.name.in_(project_names))
        if filter_non_run:
            q = q.group_by(gen_LabTable.id)
            q = q.having(count(meas_AnalysisTable.id) > 0)
        return q

    def _simple_query(self, sess, t, *args):
        if isinstance(t, tuple):
            q = sess.query(*t)
        else:
            q = sess.query(t)
        q = q.join(*args)
        return q

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

    def _get_paginated_analyses(self, q, limit=None, offset=None,
                                include_invalid=False, count_only=False):

        if not include_invalid:
            q = q.filter(meas_AnalysisTable.tag != 'invalid')

        q = q.order_by(meas_AnalysisTable.analysis_timestamp.asc())
        tc = int(q.count())
        if not tc:
            self.debug(compile_query(q))

        if count_only:
            return tc

        if limit:
            q = q.limit(limit)
        if offset:

            if offset < 0:
                offset = max(0, tc + offset)

            q = q.offset(offset)

        return self._query_all(q), tc

    def _make_hash(self, txt):
        if isinstance(txt, dict):
            txt = repr(frozenset(txt.items()))

        ha = self._hash_factory(txt)
        return ha.hexdigest()

    def _hash_factory(self, text):
        return hashlib.md5(text)

    def _append_filters(self, f, kw):

        filters = kw.get('filters', [])
        if isinstance(f, (tuple, list)):
            filters.extend(f)
        else:
            filters.append(f)
        kw['filters'] = filters
        return kw

    def _append_joins(self, f, kw):
        joins = kw.get('joins', [])
        if isinstance(f, (tuple, list)):
            joins.extend(f)
        else:
            joins.append(f)
        kw['joins'] = joins
        return kw

    def _get_date_range(self, q, hours=0):
        lan = q.order_by(meas_AnalysisTable.analysis_timestamp.asc()).first()
        han = q.order_by(meas_AnalysisTable.analysis_timestamp.desc()).first()

        lan = datetime.now() if not lan else lan[0]
        han = datetime.now() if not han else han[0]
        td = timedelta(hours=hours)
        return lan - td, han + td


# if __name__ == '__main__':
#     from pychron.core.helpers.logger_setup import logging_setup
#
#     logging_setup('ia')
#     ia = IsotopeAdapter(
#
#         # name='isotopedb_dev_migrate',
#         # name='isotopedb_FC2',
#         name='isotopedb_dev',
#         username='root',
#         password='Argon',
#         host='localhost',
#         kind='mysql'
#         # name='/Users/ross/Sandbox/exprepo/root/isotopedb.sqlite',
#         #                        name=paths.isotope_db,
#         #                        kind='sqlite'
#     )
#
#     if ia.connect():
#         dbs = IsotopeAnalysisSelector(db=ia,
#                                       # style='simple'
#         )
#         # repo = Repository(root=paths.isotope_dir)
#         # repo = Repository(root='/Users/ross/Sandbox/importtest')
#         # repo = ZIPRepository(root='/Users/ross/Sandbox/importtest/archive004.zip')
#         #        dbs.set_data_manager(kind='local',
#         #                             repository=repo,
#         #                             workspace_root=paths.default_workspace_dir
#         #                             )
#         #    dbs._execute_query()
#         #        dbs.load_recent()
#         dbs.load_last(n=100)
#
#         dbs.configure_traits()
#         #    ia.add_user(project=p, name='mosuer', commit=True)
#         #    p = ia.get_project('Foo3')
#         #    m = ia.get_material('sanidine')
#         #    ia.add_sample(name='FC-7sdh2n', project=p, material=m, commit=True)
#         # ===========================================================================
#         # test getting
#         # ===========================================================================
#         #    print ia.get_user('mosuer').id
# ============= EOF =============================================
