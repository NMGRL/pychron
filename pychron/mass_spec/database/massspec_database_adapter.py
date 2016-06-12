# ===============================================================================
# Copyright 2011 Jake Ross
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

# =============enthought library imports=======================
from traits.api import provides
# =============standard library imports ========================
import binascii
import math

from sqlalchemy.sql.expression import func, distinct
from uncertainties import std_dev, nominal_value

# =============local library imports  ==========================
from pychron.entry.iimport_source import IImportSource
from pychron.mass_spec.database.massspec_orm import IsotopeResultsTable, \
    AnalysesChangeableItemsTable, BaselinesTable, DetectorTable, \
    IsotopeTable, AnalysesTable, \
    IrradiationPositionTable, SampleTable, \
    PeakTimeTable, DetectorTypeTable, DataReductionSessionTable, \
    PreferencesTable, DatabaseVersionTable, FittypeTable, \
    BaselinesChangeableItemsTable, SampleLoadingTable, MachineTable, \
    AnalysisPositionTable, LoginSessionTable, RunScriptTable, \
    IrradiationChronologyTable, IrradiationLevelTable, IrradiationProductionTable, ProjectTable, MaterialTable, PDPTable
from pychron.database.core.database_adapter import DatabaseAdapter
from pychron.database.core.functions import delete_one
from pychron.pychron_constants import INTERFERENCE_KEYS


class MissingAliquotPychronException(BaseException):
    pass


PR_KEYS = ('Ca3637', 'Ca3637Er',
           'Ca3937', 'Ca3937Er',
           'K4039', 'K4039Er',
           'P36Cl38Cl', 'P36Cl38ClEr',
           'Ca3837', 'Ca3837Er',
           'K3839', 'K3839Er',
           'K3739', 'K3739Er',
           'ClOverKMultiplier', 'ClOverKMultiplierEr',
           'CaOverKMultiplier', 'CaOverKMultiplierEr')


@provides(IImportSource)
class MassSpecDatabaseAdapter(DatabaseAdapter):
    # selector_klass = MassSpecSelector
    test_func = 'get_database_version'
    kind = 'mysql'

    def __init__(self, bind=False, *args, **kw):
        super(MassSpecDatabaseAdapter, self).__init__(*args, **kw)
        if bind:
            self.bind_preferences()

    def bind_preferences(self):
        from apptools.preferences.preference_binding import bind_preference

        prefid = 'pychron.massspec.database'
        bind_preference(self, 'host', '{}.host'.format(prefid))
        bind_preference(self, 'username', '{}.username'.format(prefid))
        bind_preference(self, 'password', '{}.password'.format(prefid))
        bind_preference(self, 'name', '{}.name'.format(prefid))

    # @property
    # def selector_klass(self):
    # # lazy load selector klass.
    #     from pychron.database.selectors.massspec_selector import MassSpecSelector
    #
    #     return MassSpecSelector
    def get_import_spec(self, name):
        from pychron.entry.import_spec import ImportSpec, Irradiation, Level, \
            Sample, Project, Position, Production
        spec = ImportSpec()

        i = Irradiation()
        i.name = name

        spec.irradiation = i

        with self.session_ctx():
            chrons = self.get_chronology_by_irradname(name)
            i.doses = [(1.0, ci.StartTime, ci.EndTime) for ci in chrons]

            levels = self.get_irradiation_levels(name)
            nlevels = []
            for dbl in levels:
                level = Level()
                level.name = dbl.Level

                prod = Production()
                dbprod = dbl.production
                prod.name = dbprod.Label.replace(' ', '_')

                for attr in INTERFERENCE_KEYS:
                    try:
                        setattr(prod, attr, (getattr(dbprod, attr),
                                             getattr(dbprod, '{}Er'.format(attr))))
                    except AttributeError:
                        pass

                prod.Ca_K = (dbprod.CaOverKMultiplier, dbprod.CaOverKMultiplierEr)
                prod.Cl_K = (dbprod.ClOverKMultiplier, dbprod.ClOverKMultiplierEr)
                prod.Cl3638 = (dbprod.P36Cl38Cl, dbprod.P36Cl38ClEr)

                level.production = prod
                level.holder = dbl.SampleHolder

                pos = []
                for ip in self.get_irradiation_positions(name, level.name):
                    dbsam = ip.sample
                    s = Sample()
                    s.name = dbsam.Sample
                    s.material = ip.Material

                    pp = Project()
                    pp.name = ip.sample.project.Project
                    pp.principal_investigator = ip.sample.project.PrincipalInvestigator
                    s.project = pp

                    p = Position()
                    p.sample = s
                    p.position = ip.HoleNumber
                    p.identifier = ip.IrradPosition
                    p.j = ip.J
                    p.j_err = ip.JEr
                    p.note = ip.Note
                    p.weight = ip.Weight

                    pos.append(p)
                level.positions = pos
                nlevels.append(level)

            i.levels = nlevels
        return spec

    # ===============================================================================
    # getters
    # ===============================================================================
    def get_latest_preferences(self, isoid):
        with self.session_ctx() as sess:
            q = sess.query(PreferencesTable)
            q = q.join(AnalysesChangeableItemsTable)
            q = q.join(DataReductionSessionTable)
            q = q.join(IsotopeTable)

            q = q.filter(IsotopeTable.IsotopeID == isoid)

            q = q.order_by(DataReductionSessionTable.SessionDate.desc())
            q = q.limit(1)

            return self._query_first(q, verbose_query=True)

    def get_pdp(self, isoid):
        with self.session_ctx() as sess:
            q = sess.query(PDPTable)
            q = q.filter(PDPTable.IsotopeID == isoid)
            q = q.order_by(PDPTable.LastSaved.desc())
            return self._query_first(q)

    def get_baseline_changeable_item(self, bslnid):
        return self._retrieve_item(BaselinesChangeableItemsTable, bslnid, 'BslnID')

    def get_material(self, name):
        return self._retrieve_item(MaterialTable, name, 'Material')

    def get_project(self, name):
        return self._retrieve_item(ProjectTable, name, 'Project')

    def get_irradiation_positions(self, name, level):
        with self.session_ctx() as sess:
            q = sess.query(IrradiationPositionTable)
            q = q.filter(IrradiationPositionTable.IrradiationLevel == '{}{}'.format(name, level))
            return q.all()

    def get_production_ratio_by_id(self, idn):
        return self._retrieve_item(IrradiationProductionTable, idn, 'ProductionRatiosID')

    def get_production_ratio_by_level(self, irrad, name):
        with self.session_ctx() as sess:
            q = sess.query(IrradiationLevelTable)
            q = q.filter(IrradiationLevelTable.IrradBaseID == irrad)
            q = q.filter(IrradiationLevelTable.Level == name)
            return q.one().production

    def get_production_ratio_by_irradname(self, name):
        with self.session_ctx() as sess:
            q = sess.query(IrradiationLevelTable)
            q = q.filter(IrradiationLevelTable.IrradBaseID == name)
            irrad = q.all()
            if irrad:
                return irrad[-1].production

    def get_irradiation_level_names(self, *args, **kw):
        names = []
        with self.session_ctx():
            levels = self.get_irradiation_levels(*args, **kw)
            if levels:
                names = [li.Level for li in levels]
        return names

    def get_irradiation_levels(self, name, levels=None):
        with self.session_ctx() as sess:
            q = sess.query(IrradiationLevelTable)
            q = q.filter(IrradiationLevelTable.IrradBaseID == name)
            if levels:
                if not hasattr(levels, '__iter__'):
                    levels = (levels,)

                q = q.filter(IrradiationLevelTable.Level.in_(levels))

            return self._query_all(q)

    def get_chronology_by_irradname(self, name):
        with self.session_ctx() as sess:
            q = sess.query(IrradiationChronologyTable)
            q = q.filter(IrradiationChronologyTable.IrradBaseID == name)
            q = q.order_by(IrradiationChronologyTable.EndTime.asc())
            return q.all()

    def get_irradiation_exists(self, name):
        with self.session_ctx() as sess:
            q = sess.query(IrradiationLevelTable.IrradBaseID)
            q = q.filter(IrradiationLevelTable.IrradBaseID == name)
            r = self._query_one(q)
            return r is not None

    def get_irradiation_names(self):
        with self.session_ctx() as sess:
            q = sess.query(distinct(IrradiationLevelTable.IrradBaseID))
            vs = q.all()
            if vs:
                vs = sorted([vi[0] for vi in vs], reverse=True)
            return vs

    def get_analyses(self, **kw):
        return self._get_items(AnalysesTable, globals(), **kw)

    def get_samples(self, **kw):
        return self._get_items(SampleTable, globals(), **kw)

    def get_sample_loading(self, value):
        return self._retrieve_item(SampleLoadingTable, value,
                                   key='SampleLoadingID')

    def get_login_session(self, value):
        return self._retrieve_item(LoginSessionTable, value, key='LoginSessionID')

    def get_latest_analysis(self, labnumber, aliquot=None):
        """
            return the analysis with the greatest aliquot with this labnumber
        """
        with self.session_ctx() as sess:
            if aliquot is not None:
                # sql = 'SELECT `AnalysesTable`.`Aliquot`, `AnalysesTable`.`Increment` ' \
                #       'FROM `AnalysesTable` ' \
                #       'WHERE `AnalysesTable`.`RID` LIKE "{}-{:02n}%" ' \
                #       'ORDER BY `AnalysesTable`.`AnalysisID` DESC LIMIT 1'.format(labnumber, aliquot)
                sql = 'SELECT AnalysesTable.Aliquot_pychron, AnalysesTable.Increment ' \
                      'FROM AnalysesTable ' \
                      'WHERE AnalysesTable.RID LIKE "{}-{:02d}%" ' \
                      'ORDER BY AnalysesTable.AnalysisID DESC LIMIT 1'.format(labnumber, aliquot)
                v = sess.execute(sql)
                if v is not None:
                    r = v.fetchone()
                    if r:
                        a, s = r
                        try:
                            a = int(a)
                            return a, s
                        except ValueError:
                            raise MissingAliquotPychronException()
            else:
                # !!!!!
                # this is an issue. mass spec stores the aliquot as an varchar instead of an integer
                # sorts lexicographically instead of numerically
                # so '100'<'001'
                # http://stackoverflow.com/questions/4686849/sorting-varchar-field-numerically-in-mysql
                # use option 2. this is a low use query and performance is not and issue
                # switch to option 3. if performance increase is desired
                # !!!!!
                # q = q.order_by(cast(AnalysesTable.Aliquot, INTEGER).desc())

                sql = 'SELECT AnalysesTable.Aliquot_pychron, AnalysesTable.Increment ' \
                      'FROM AnalysesTable ' \
                      'WHERE AnalysesTable.RID LIKE "{}%" ' \
                      'ORDER BY AnalysesTable.Aliquot_pychron DESC LIMIT 1'.format(labnumber)

                v = sess.execute(sql)
                if v is not None:
                    r = v.fetchone()
                    if r:
                        a, s = r
                        a = a or 0
                        return int(a), s

    def get_analysis_rid(self, rid):
        return self._retrieve_item(AnalysesTable, rid, key='RID')

    def get_analysis(self, value, aliquot=None, step=None, **kw):
        if isinstance(value, str):
            if value.startswith('a'):
                value = -2
            elif value.startswith('ba'):
                value = -1

        key = 'IrradPosition'
        if aliquot:
            if step:
                key = (key, 'Aliquot', 'Increment')
                value = (value, aliquot, step)
            else:
                key = (key, 'Aliquot')
                value = (value, aliquot)

        return self._retrieve_item(AnalysesTable, value,
                                   key=key, **kw)

    def get_irradiation_position(self, value):
        return self._retrieve_item(IrradiationPositionTable, value,
                                   key='IrradPosition', )

    def get_irradiation_level(self, name, level):
        return self._retrieve_item(IrradiationLevelTable,
                                   value=(name, level),
                                   key=('IrradBaseID', 'Level'))

    def get_sample(self, value):
        return self._retrieve_item(SampleTable, value, key='Sample')

    def get_detector_type(self, value):
        return self._retrieve_item(DetectorTypeTable, value, key='Label')

    #    @get_first
    def get_detector(self, name):
        return self._retrieve_first(DetectorTable, name,
                                    key='Label',
                                    order_by=DetectorTable.DetectorID.desc())

    def get_isotope(self, value):
        return self._retrieve_item(IsotopeTable, value, key='AnalysisID')

    def get_data_reduction_session(self, value):
        return self._retrieve_item(DataReductionSessionTable, value,
                                   key='DataReductionSessionID')

    def get_preferences_set(self, value):
        return self._retrieve_item(PreferencesTable, value, key='PreferenceSetID')

    def get_system(self, value):
        return self._retrieve_item(MachineTable, value, key='Label')

    def get_fittype(self, label):
        """
            convert label to mass spec format
        """
        if isinstance(label, str):
            label = label.capitalize()
            if label.startswith('Average'):
                label = 'Average Y'

        fit = self._get_fittype(label, )
        if fit is None:
            fit = 0
        else:
            fit = fit.Fit

        return fit

    def get_runscript(self, value):
        return self._retrieve_item(RunScriptTable, value, key='RunScriptID', )

    def get_irradiation_level(self, irrad, name):
        with self.session_ctx() as sess:
            q = sess.query(IrradiationLevelTable)
            q = q.filter(IrradiationLevelTable.Level == name)
            q = q.filter(IrradiationLevelTable.IrradBaseID == irrad)
            return self._query_one(q)

    def get_database_version(self, **kw):
        ver = 0
        with self.session_ctx() as sess:
            q = sess.query(DatabaseVersionTable)
            item = self._query_one(q, **kw)
            if item:
                ver = item.Version

        self.debug('MassSpec Database Version: {}'.format(ver))
        return ver

    # ===============================================================================
    # adders
    # ===============================================================================
    def add_project(self, name):
        with self.session_ctx():
            obj = ProjectTable(Project=name)
            return self._add_item(obj)

    def add_material(self, name):
        with self.session_ctx():
            obj = MaterialTable(Material=name)
            return self._add_item(obj)

    def add_sample(self, name):
        with self.session_ctx():
            obj = SampleTable(Sample=name, ProjectID=1)
            return self._add_item(obj)

    def add_production_ratios(self, prdict):
        """
            keys =


        :param prdict:
        :return:
        """
        obj = IrradiationProductionTable(**prdict)
        return self._add_item(obj)

    def add_irradiation_level(self, irrad, name, holder, production, **kw):
        if not self.get_irradiation_level(irrad, name):
            production = self.get_production_ratio_by_id(production)

            i = IrradiationLevelTable(IrradBaseID=irrad,
                                      Level=name,
                                      SampleHolder=holder,
                                      # ProductionRatiosID=production,
                                      **kw)
            i.production = production

            return self._add_item(i)

    def add_irradiation_position(self, identifier, irrad_level, hole,
                                 material='', sample=6, j=1e-4, jerr=1e-7, note=''):
        """

        :param identifier:
        :param irrad_level: str e.g NM-176A
        :param hole:
        :param material:
        :param sample:
        :param j:
        :param jerr:
        :return:
        """
        with self.session_ctx() as sess:
            q = sess.query(IrradiationPositionTable)
            q = q.filter(IrradiationPositionTable.IrradPosition == identifier)
            if not self._query_one(q):
                i = IrradiationPositionTable(IrradPosition=identifier,
                                             IrradiationLevel=irrad_level,
                                             HoleNumber=hole,
                                             Note=note,
                                             Material=material,
                                             SampleID=sample,
                                             J=j, JEr=jerr)
                return self._add_item(i)

    def add_irradiation_production(self, name, pr, ifc):
        kw = {}
        for k, v in ifc.iteritems():
            if k == 'cl3638':
                k = 'P36Cl38Cl'
            else:
                k = k.capitalize()

            kw[k] = float(nominal_value(v))
            kw['{}Er'.format(k)] = float(std_dev(v))

        kw['ClOverKMultiplier'] = pr['Cl_K']
        kw['ClOverKMultiplierEr'] = 0
        kw['CaOverKMultiplier'] = pr['Ca_K']
        kw['CaOverKMultiplierEr'] = 0
        v = binascii.crc32(''.join([str(v) for v in kw.itervalues()]))
        with self.session_ctx() as sess:
            q = sess.query(IrradiationProductionTable)
            q = q.filter(IrradiationProductionTable.ProductionRatiosID == v)
            if not self._query_one(q):
                i = IrradiationProductionTable(Label=name,
                                               ProductionRatiosID=v,
                                               **kw)
                self._add_item(i)
        return v

    def add_irradiation_chronology_segment(self, irrad, s, e):
        with self.session_ctx() as sess:
            q = sess.query(IrradiationChronologyTable)
            q = q.filter(IrradiationChronologyTable.IrradBaseID == irrad)
            q = q.filter(IrradiationChronologyTable.StartTime == s)
            q = q.filter(IrradiationChronologyTable.EndTime == e)
            if not self._query_one(q):
                i = IrradiationChronologyTable(IrradBaseID=irrad, StartTime=s, EndTime=e)
                self._add_item(i)

    def add_sample_loading(self, ms, tray):

        if isinstance(ms, str):
            ms = ms.capitalize()
            system = self.get_system(ms, )
            if system:
                ms = system.SpecSysN
            else:
                ms = 0

        sm = SampleLoadingTable(SampleHolder=tray,
                                SpecSysN=ms)
        self._add_item(sm)
        return sm

    def add_analysis_positions(self, analysis, positions):
        if positions:
            if not isinstance(positions, list):
                positions = [positions]

            analysis = self.get_analysis(analysis, )
            if analysis:
                for i, pi in enumerate(positions):
                    try:
                        pi = int(pi)
                        self._add_analysis_position(analysis, pi, i + 1)
                    except (ValueError, TypeError):
                        pass

    def add_irradiation_chronology_entry(self, irradname, start, end):
        obj = IrradiationChronologyTable(IrradBaseID=irradname,
                                         StartTime=start, EndTime=end)
        self._add_item(obj)

    def add_analysis(self, rid, aliquot, step, irradpos, runtype, **kw):
        if isinstance(aliquot, int):
            aliquot = '{:02d}'.format(aliquot)

        # query the IrradiationPositionTable
        irradpos = self.get_irradiation_position(irradpos, )
        params = dict(RID=rid,
                      Aliquot=aliquot,
                      Aliquot_pychron=int(aliquot),
                      RunDateTime=func.current_timestamp(),
                      LoginSessionID=1,
                      SpecRunType=runtype,
                      Increment=step)

        # IrradPosition cannot be null
        if irradpos is not None:
            ip = irradpos.IrradPosition
            sa = irradpos.SampleID
        else:
            ip = -2
            sa = 0

        params['RedundantSampleID'] = sa
        params['IrradPosition'] = ip
        params.update(kw)

        analysis = AnalysesTable(**params)
        self._add_item(analysis, )

        return analysis

    def add_baseline(self, blob, label, cnts, iso, **kw):
        bs = BaselinesTable(PeakTimeBlob=blob,
                            Label=label,
                            NumCnts=cnts)
        if iso is not None:
            iso.baseline = bs

        return bs

    def add_baseline_changeable_item(self, data_reduction_session_id, fit, infoblob):
        fit = self.get_fittype(fit, )

        bs = BaselinesChangeableItemsTable(Fit=fit,
                                           DataReductionSessionID=data_reduction_session_id,
                                           InfoBlob=infoblob)
        self._add_item(bs, )
        return bs

    def add_peaktimeblob(self, blob1, blob2, iso, **kw):
        iso = self.get_isotope(iso, )
        pk = PeakTimeTable(PeakTimeBlob=blob1,
                           PeakNeverBslnCorBlob=blob2)
        if iso is not None:
            iso.peak_time_series.append(pk)

        return pk

    def add_detector(self, det_type, **kw):
        dtype = self.get_detector_type(det_type, )
        d = DetectorTable(
            DetectorTypeID=dtype.DetectorTypeID,
            **kw)

        self._add_item(d, )
        return d

    def add_isotope(self, rid, detector, label, **kw):

        analysis = self.get_analysis(rid, )

        if isinstance(detector, str):
            # assume is a detector label e.i H1
            detector = self.get_detector_type(detector, )
            if detector:
                detector = detector.Label

        if detector is not None:  # and len(dettype.detectors):
            detector = self.get_detector(detector, )

        iso = IsotopeTable(Label=label, **kw)
        if analysis is not None:
            analysis.isotopes.append(iso)

        if detector is not None:
            iso.DetectorID = detector.DetectorID
            iso.BkgdDetectorID = detector.DetectorID

        self._add_item(iso, )
        return iso

    def add_isotope_result(self, isotope, data_reduction_session_id, intercept, baseline, blank, fit, detector,
                           is_blank=False):
        """
            intercept, baseline and blank should be ufloats

            mass spec does not propogate baseline error
        :param is_blank:
        """

        isotope = self.get_isotope(isotope, )

        # in mass spec intercept is baseline corrected
        # mass spec does not propagate baseline error
        # convert baseline to scalar
        baseline = nominal_value(baseline)

        intercept = intercept - baseline
        if is_blank:
            isotope_value = intercept
        else:
            # isotope is corrected for background (blank in pychron parlance)
            isotope_value = intercept - blank

        fit = self.get_fittype(fit, )

        detector = self.get_detector(detector, )

        def clean_value(x, k='nominal_value'):
            v = getattr(x, k)
            return float(v) if not (math.isnan(v) or math.isinf(v)) else 0

        i = clean_value(intercept)
        ie = clean_value(intercept, 'std_dev')

        iso = clean_value(isotope_value)
        isoe = clean_value(isotope_value, 'std_dev')

        b = clean_value(blank)
        be = clean_value(blank, 'std_dev')

        iso_r = IsotopeResultsTable(DataReductionSessionID=data_reduction_session_id,
                                    Intercept=i,
                                    InterceptEr=ie,

                                    Iso=iso,
                                    IsoEr=isoe,

                                    Bkgd=b,
                                    BkgdEr=be,

                                    BkgdDetTypeID=detector.DetectorTypeID,

                                    Fit=fit)
        if isotope:
            isotope.results.append(iso_r)

        return isotope

    def add_data_reduction_session(self, **kw):
        drs = DataReductionSessionTable(
            SessionDate=func.current_timestamp())
        self._add_item(drs, )
        return drs

    def add_login_session(self, ms, **kw):

        if isinstance(ms, str):
            ms = ms.capitalize()
            system = self.get_system(ms, )
            if system:
                ms = system.SpecSysN
            else:
                ms = 0

        drs = LoginSessionTable(SpecSysN=ms)
        self._add_item(drs, )
        return drs

    def add_changeable_items(self, rid, drs_id):
        item = AnalysesChangeableItemsTable()
        analysis = self.get_analysis(rid, )
        if analysis is not None:
            # get the lastest preferencesetid
            #            sess = self.get_session()
            #            q = sess.query(PreferencesTable)
            #            q = q.order_by(PreferencesTable.PreferencesSetID.desc())
            #            q = q.limit(1)
            #            pref = q.one()

            pref = self.get_preferences_set(None, )
            if pref is not None:
                pref.changeable_items.append(item)
            else:
                item.PreferencesSetID = 0
            item.AnalysisID = analysis.AnalysisID
            #            analysis.changeable.append(item)

            item.DataReductionSessionID = drs_id
            #            drs.changeable_items.append(item)
            self._add_item(item, )

        return item

    def add_runscript(self, label, text, **kw):
        """
            runscripttable does not autoincrement primary key

            uses a crc-32 of text as the RunScriptID
        """
        crc = binascii.crc32(text)
        rs = self.get_runscript(crc)
        if rs is None:
            rs = RunScriptTable(RunScriptID=crc, Label=label, TheText=text)
            self._add_item(rs)

        return rs

    # ===============================================================================
    # deleters
    # ===============================================================================
    @delete_one
    def delete_analysis(self, rid):
        return AnalysesTable, 'RID'

    # ===============================================================================
    # private
    # ===============================================================================
    def _get_fittype(self, value):
        return self._retrieve_item(FittypeTable, value, key='Label', )

    def _add_analysis_position(self, analysis, pi, po):
        a = AnalysisPositionTable(Hole=pi, PositionOrder=po)
        analysis.positions.append(a)


if __name__ == '__main__':
    from pychron.core.helpers.logger_setup import logging_setup

    logging_setup('ia')
    ia = MassSpecDatabaseAdapter()
    ia.connect()

    #    ia.selector_factory()
    # dbs = ia.selector
    # dbs.load_recent()
    # dbs.configure_traits()
# ==================EOF======================================================
