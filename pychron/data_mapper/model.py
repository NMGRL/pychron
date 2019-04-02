# ===============================================================================
# Copyright 2016 Jake Ross
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
from __future__ import absolute_import

from traits.api import HasTraits, Str, Int, Bool, Any, Button, Instance, List, Dict

from pychron.core.fuzzyfinder import fuzzyfinder
from pychron.core.helpers.iterfuncs import groupby_key
from pychron.core.progress import open_progress
from pychron.dvc.dvc_persister import DVCPersister
from pychron.entry.entry_views.repository_entry import RepositoryIdentifierEntry
from pychron.loggable import Loggable


class IrradiationItem(HasTraits):
    name = Str


class ImportedIrradiation(IrradiationItem):
    skipped = Bool
    nlevels = Int
    npositions = Int
    nsamples = Int
    nprojects = Int
    nmaterials = Int
    nprincipal_investigators = Int


class Mapper:
    irradiation_project = None

    def material(self, m):
        if m.lower() in ('san', 'sandine', 'sanidine'):
            m = 'Sanidine'
        elif m.lower() in ('wr',):
            m = 'Whole Rock'
        elif m.lower() in ('gm', 'groundmass'):
            m = 'Groundmass'
        elif m.lower() in ('gmc', 'groundmass concentrate'):
            m = 'Groundmass Concentrate'
        elif m.lower() in ('plag', 'plagioclase'):
            m = 'Plagioclase'
        elif m.lower() in ('hbl', 'hornblende'):
            m = 'Hornblende'
        elif m.lower() in ('phlogopite',):
            m = 'Phlogopite'
        elif m.lower() in ('bi', 'biotite'):
            m = 'Biotite'
        elif m.lower() in ('musc', 'muscovite'):
            m = 'Muscovite'
        elif m.lower() in ('kspar'):
            m = 'K-Feldspar'

        return m

    def project(self, p):
        if p == 'J-Curve':
            p = 'Irradiation-{}'.format(self.irradiation_project)

        return p

    def principal_investigator(self, p):
        p = p.strip()
        if not p:
            p = 'NMGRL'

        return p


class BaseDVCImporterModel(Loggable):
    dvc = Instance('pychron.dvc.dvc.DVC')
    sources = Dict

    source = Any
    repository_identifier = Str
    repository_identifiers = List


class DVCIrradiationImporterModel(BaseDVCImporterModel):
    irradiations = List
    available_irradiations = List

    imported_irradiations = List
    selected = List
    scroll_to_row = Int

    filter_str = Str
    clear_filter_button = Button

    def __init__(self, *args, **kw):
        super(DVCIrradiationImporterModel, self).__init__(*args, **kw)
        self.mapper = Mapper()

    def do_import(self):
        self.debug('doing import')

        if self.source.selectable:
            if not self.selected:
                self.information_dialog('Please select an Irradiation to import')
                return

            self.debug('Selected Irradiations')
            for irrad in self.selected:
                self.debug(irrad.name)

            specs = [(i.name, self.source.get_irradiation_import_spec(i.name)) for i in self.selected]
        else:
            spec = self.source.get_irradiation_import_spec()
            specs = [(spec.irradiation.name, spec)]

        prog = self._open_progress(specs)

        for irradname, spec in specs:
            self.mapper.irradiation_project = irradname
            if not spec:
                self.warning('Failed to make import spec for {}'.format(irradname))
                continue

            self._import_irradiation(spec.irradiation)

        prog.close()

    def _import_irradiation(self, irrad):
        name = irrad.name
        self.debug('importing {}'.format(name))
        self._progress.change_message('Importing {}'.format(name))
        dvc = self.dvc

        dvc.add_irradiation(name, irrad.doses)
        self._active_import = ImportedIrradiation(name=name)
        for level in irrad.levels:
            self._import_level(name, level)

        dvc.meta_repo.add_unstaged()
        dvc.meta_repo.commit('Imported {}'.format(name))

        self.imported_irradiations.append(self._active_import)

    def _import_level(self, irradname, level):
        name = level.name
        self.debug('importing level {}'.format(name))
        self._progress.change_message('Importing {} {}'.format(irradname, name))
        dvc = self.dvc

        dvc.add_production(irradname, level.production.name, level.production)
        if dvc.add_irradiation_level(name, irradname, level.holder, level.production.name,
                                     z=level.z,
                                     note=level.note):
            self._active_import.nlevels += 1

        for p in level.positions:
            self._import_position(irradname, level, p)

    def _import_position(self, irradname, level, p):
        self.debug('importing position {} {}'.format(p.position, p.identifier))
        self._progress.change_message('Importing {} {} {}({})'.format(irradname, level.name, p.position, p.identifier))
        dvc = self.dvc
        db = dvc.db
        sam = p.sample
        dbsam = None
        if sam:
            material = self.mapper.material(sam.material)
            added = dvc.add_material(material)
            if added:
                self._active_import.nmaterials += 1
            db.commit()

            principal_investigator = self.mapper.principal_investigator(sam.project.principal_investigator)
            added = dvc.add_principal_investigator(principal_investigator)
            if added:
                self._active_import.nprincipal_investigators += 1
            db.commit()

            project = self.mapper.project(sam.project.name)
            added = dvc.add_project(project, principal_investigator)
            if added:
                self._active_import.nprojects += 1
            db.commit()

            added = dvc.add_sample(sam.name, project, material)
            if added:
                self._active_import.nsamples += 1
            db.commit()
            dbsam = db.get_sample(sam.name, project, material)

        added = dvc.add_irradiation_position(irradname, level.name, p.position,
                                             identifier=p.identifier,
                                             sample=dbsam,
                                             note=p.note,
                                             weight=p.weight)
        if added:
            self._active_import.npositions += 1
        dvc.update_flux(irradname, level.name, p.position, p.identifier, p.j, p.j_err, 0, 0)

    def _open_progress(self, specs):
        n = len(specs)
        for _, i in specs:
            n += len(i.irradiation.levels)
            for l in i.irradiation.levels:
                n += len(l.positions)

        prog = open_progress(n)
        self._progress = prog
        return prog

    def _clear_filter_button_fired(self):
        self.filter_str = ''

    def _filter_str_changed(self, new):
        if new:
            items = fuzzyfinder(new, self.oavailable_irradiations, attr='name')
        else:
            items = self.oavailable_irradiations

        self.available_irradiations = items

    # def _source_changed(self):
    #     if self.source.connect():
    #         self.available_irradiations = [IrradiationItem(name=i) for i in self.source.get_irradiation_names()]
    #     else:
    #         self.available_irradiations = []
    #
    #     self.oavailable_irradiations = self.available_irradiations


class DVCAnalysisImporterModel(BaseDVCImporterModel):
    mass_spectrometer = Str
    extract_device = Str
    principal_investigator = Str

    def __init__(self, *args, **kw):
        super(DVCAnalysisImporterModel, self).__init__(*args, **kw)
        self.refresh_repository_identifiers()

    def refresh_repository_identifiers(self):
        self.repository_identifiers = self.dvc.get_repository_identifiers()

    def add_repository(self):
        dest = self.dvc
        a = RepositoryIdentifierEntry(dvc=dest)

        with dest.session_ctx(use_parent_session=False):
            a.available = self.repository_identifiers
            a.principal_investigators = dest.get_principal_investigator_names()

        if a.do():
            self.refresh_repository_identifiers()

    def do_import(self):
        self.debug('doing import')

        aspecs = self.source.get_analysis_import_specs()
        dest = self.dvc
        persister = DVCPersister(dvc=dest)
        persister.initialize(self.repository_identifier)

        def key(s):
            return s.run_spec.irradiation

        for irrad, iaspec in groupby_key(aspecs, key):
            if not dest.get_irradiation(irrad):
                self.warning_dialog('No Irradiation "{}". Please import the irradiation'.format(irrad))
                continue

            for aspec in iaspec:
                rspec = aspec.run_spec

                rspec.repository_identifier = self.repository_identifier
                rspec.mass_spectrometer = self.mass_spectrometer
                rspec.principal_investigator = self.principal_investigator

                if dest.get_analysis_runid(rspec.identifier, rspec.aliquot, rspec.step):
                    self.warning('{} already exists'.format(rspec.runid))
                    continue

                self._add_mass_spectrometer(aspec)
                self._add_extract_device(aspec)
                self._add_principal_investigator(aspec)
                self._add_material(aspec)
                self._add_project(aspec)
                self._add_sample(aspec)
                self._add_position(aspec)

                persister.per_spec_save(aspec, commit=True,
                                        commit_tag='Transfer:{}'.format(self.source.url()),
                                        push=False)

            persister.push()

    def _add_position(self, spec):
        rspec = spec.run_spec
        dest = self.dvc
        idn = rspec.identifier
        if not dest.get_identifier(idn):
            with dest.session_ctx():
                irrad = rspec.irradiation
                level = rspec.irradiation_level
                pos = rspec.irradiation_position

                ip = dest.db.add_irradiation_position(irrad, level, pos, idn)
                sample = dest.get_sample(rspec.sample, rspec.project, rspec.principal_investigator, rspec.material)
                ip.sample = sample

                dest.update_flux(irrad, level, pos, idn, spec.j, spec.j_err, 0, 0)
                dest.commit()

    def _add_sample(self, spec):
        spec = spec.run_spec
        dest = self.dvc
        if not dest.get_sample(spec.sample, spec.project, spec.principal_investigator,
                               spec.material):
            self.debug('adding sample {}'.format(spec.sample))
            dest.add_sample(spec.sample, spec.project, spec.principal_investigator,
                            spec.material)
            dest.commit()

    def _add_project(self, spec):
        spec = spec.run_spec
        dest = self.dvc
        if not dest.get_project(spec.project, spec.principal_investigator):
            self.debug('adding project {},{}'.format(spec.project, spec.principal_investigator))
            dest.add_project(spec.project, spec.principal_investigator)
            dest.commit()

    def _add_material(self, spec):
        dest = self.dvc
        mat = spec.run_spec.material
        if not dest.get_material(mat):
            self.debug('adding material {}'.format(mat))
            dest.add_material(mat)
            dest.commit()

    def _add_principal_investigator(self, spec):
        dest = self.dvc
        pi = spec.run_spec.principal_investigator
        if not dest.get_principal_investigator(pi):
            self.debug('adding principal investigator {}'.format(pi))
            dest.add_principal_investigator(pi)
            dest.commit()

    def _add_mass_spectrometer(self, spec):
        dest = self.dvc
        ms = spec.run_spec.mass_spectrometer
        if not dest.get_mass_spectrometer(ms):
            self.debug('adding mass spectrometer {}'.format(ms))
            dest.add_mass_spectrometer(ms)
            dest.commit()

    def _add_extract_device(self, spec):
        ed = spec.run_spec.extract_device
        if not ed:
            ed = 'No Extract Device'

        dest = self.dvc
        if not dest.get_extraction_device(ed):
            self.debug('adding extract device {}'.format(ed))
            dest.add_extraction_device(ed)
            dest.commit()

# ============= EOF =============================================
