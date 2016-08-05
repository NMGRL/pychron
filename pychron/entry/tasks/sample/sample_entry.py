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
import os
import re

import yaml
from traits.api import HasTraits, Str, Bool, Property, Event, cached_property, \
    Button, String, Instance, List

from pychron.dvc.dvc_irradiationable import DVCAble
from pychron.paths import paths

PI_REGEX = re.compile(r'^[A-Z]+\w+(,[A-Z]{1})*$')
MATERIAL_REGEX = re.compile(r'^[A-Z]+[\w%/\+-_]+$')


class PIStr(String):
    def validate(self, obj, name, value):
        if not PI_REGEX.match(value) and name != 'NMGRL':
            return self.error(obj, name, value)
        else:
            return value


class MaterialStr(String):
    def validate(self, obj, name, value):
        if not MATERIAL_REGEX.match(value):
            return self.error(obj, name, value)
        else:
            return value


class ProjectStr(String):
    pass


class Spec(HasTraits):
    name = Str
    added = Bool


class PISpec(Spec):
    def todump(self):
        return {'name': str(self.name)}

    @classmethod
    def fromdump(cls, d):
        obj = cls()
        obj.name = d['name']
        return obj


class MaterialSpec(Spec):
    name = Str
    grainsize = Str

    def todump(self):
        return {'name': str(self.name), 'grainsize': str(self.grainsize)}

    @classmethod
    def fromdump(cls, d):
        obj = cls()
        obj.name = d['name']
        obj.grainsize = d['grainsize']
        return obj


class ProjectSpec(Spec):
    principal_investigator = Instance(PISpec)

    def todump(self):
        return {'name': str(self.name), 'principal_investigator': self.principal_investigator.todump()}

    @classmethod
    def fromdump(cls, d, ps):
        obj = cls()
        obj.name = d['name']
        pi = d['principal_investigator']['name']
        for pp in ps:
            if pp.name == pi:
                obj.principal_investigator = pp
                break
        return obj


class SampleSpec(Spec):
    project = Instance(ProjectSpec)
    material = Instance(MaterialSpec)

    def todump(self):
        return {'name': str(self.name), 'project': self.project.todump(), 'material': self.material.todump()}

    @classmethod
    def fromdump(cls, d, pps, ms):
        obj = cls()
        obj.name = d['name']
        project = d['project']
        pname = project['name']
        piname = project['principal_investigator']['name']
        for pp in pps:
            print pname, pp.name, piname, pp.principal_investigator.name
            if pp.name == pname and pp.principal_investigator.name == piname:
                obj.project = pp
                break

        m = d['material']
        mname, grainsize = m['name'], m['grainsize']
        for mi in ms:
            if mi.name == mname and mi.grainsize == grainsize:
                obj.material = mi
                break
        return obj


class SampleEntry(DVCAble):
    principal_investigator = PIStr(enter_set=True, auto_set=False)
    principal_investigators = Property(depends_on='refresh_pis')
    refresh_pis = Event

    project = ProjectStr(enter_set=True, auto_set=False)
    projects = Property(depends_on='refresh_projects')
    refresh_projects = Event

    material = MaterialStr(enter_set=True, auto_set=False)
    materials = Property(depends_on='refresh_materials')
    refresh_materials = Event
    grainsize = Str
    grainsizes = Property(depends_on='refresh_grainsizes')
    refresh_grainsizes = Event

    sample = Str

    add_principal_investigator_button = Button
    add_project_button = Button
    add_sample_button = Button
    add_button = Button
    add_material_button = Button

    project_enabled = Property(depends_on='principal_investigator')
    sample_enabled = Property(depends_on='principal_investigator, project, material')

    refresh_table = Event

    _samples = List
    _projects = List
    _materials = List
    _principal_investigators = List

    def activated(self):
        self.refresh_pis = True
        self.refresh_materials = True
        self.refresh_projects = True
        self.refresh_grainsizes = True

    def prepare_destroy(self):
        self._backup()

    def save(self):
        self._backup()
        self._save()

    def load(self, p):
        with open(p, 'r') as rfile:
            obj = yaml.load(rfile)
            self._principal_investigators = ps = [PISpec.fromdump(p) for p in obj['principal_investigators']]
            self._materials = ms = [MaterialSpec.fromdump(p) for p in obj['materials']]

            self._projects = pps = [ProjectSpec.fromdump(p, ps) for p in obj['projects']]
            self._samples = [SampleSpec.fromdump(p, pps, ms) for p in obj['samples']]

    def dump(self, p):
        """
        only dump if at least one value is not null
        :param p:
        :return:
        """
        obj = self._assemble()
        if obj:
            with open(p, 'w') as wfile:
                yaml.dump(obj, wfile)

    # private
    def _backup(self):
        p = os.path.join(paths.sample_dir, '.last.yaml')
        self.dump(p)

    def _assemble(self):
        ps = [p.todump() for p in self._principal_investigators]
        ms = [p.todump() for p in self._materials]
        pps = [p.todump() for p in self._projects]
        ss = [p.todump() for p in self._samples]
        if ps or ms or pps or ss:
            obj = {'principal_investigators': ps,
                   'projects': pps,
                   'materials': ms,
                   'samples': ss}

            return obj

    def _save(self):
        self.debug('saving sample info')
        dvc = self.dvc
        for p in self._principal_investigators:
            if dvc.add_principal_investigator(p.name):
                p.added = True

        for p in self._projects:
            if dvc.add_project(p.name, p.principal_investigator.name):
                p.added = True

        for m in self._materials:
            if dvc.add_material(m.name, m.grainsize or None):
                m.added = True

        for s in self._samples:
            if dvc.add_sample(s.name, s.project.name, s.material.name, s.material.grainsize or None):
                s.added = True

        self.refresh_table = True

    def _get_principal_investigator_spec(self):
        for p in self._principal_investigators:
            if p.name == self.principal_investigator:
                return p
        else:
            p = PISpec(name=self.principal_investigator)
            self._principal_investigators.append(p)
            return p

    def _get_project_spec(self):
        if self.project:
            pspec = self._get_principal_investigator_spec()
            for p in self._projects:
                if p.name == self.project and p.principal_investigator.name == pspec.name:
                    return p
            else:
                p = ProjectSpec(name=self.project, principal_investigator=pspec)
                self._projects.append(p)
                return p

    def _get_material_spec(self):
        if self.material:
            for p in self._materials:
                if p.name == self.material:
                    if not self.grainsize or self.grainsize == p.grainsize:
                        return p
            else:
                m = MaterialSpec(name=self.material, grainsize=self.grainsize)
                self._materials.append(m)
                return m

    # handlers
    def _add_sample_button_fired(self):
        if self.sample:

            material_spec = self._get_material_spec()
            if not material_spec:
                self.information_dialog('Please enter a material for this sample')
                return

            project_spec = self._get_project_spec()
            if not project_spec:
                self.information_dialog('Please enter a project for this sample')
                return

            self._samples.append(SampleSpec(name=self.sample,
                                            project=project_spec,
                                            material=material_spec))
            self._backup()

    def _add_project_button_fired(self):
        if self.project:
            pispec = self._get_principal_investigator_spec()
            for p in self._projects:
                if p.name == self.project and p.principal_investigator.name == pispec.name:
                    break
            else:
                self._projects.append(ProjectSpec(name=self.project,
                                                  principal_investigator=pispec))
                self._backup()

    def _add_material_button_fired(self):
        if self.material:
            from pychron.entry.dvc_import.model import Mapper
            mapper = Mapper()
            nm = mapper.material(self.material)
            if nm != self.material:
                msg = 'Pychron suggests changing "{}" to "{}". \n\n' \
                      'Would you like to continue?'.format(self.material, nm)
                if not self.confirmation_dialog(msg):
                    return
                self.material = nm

            for m in self._materials:
                if m.name == self.material and m.grainsize == self.grainsize:
                    break
            else:
                self._materials.append(MaterialSpec(name=self.material,
                                                    grainsize=self.grainsize))
                self._backup()

    def _add_principal_investigator_button_fired(self):
        if self.principal_investigator:
            for p in self._principal_investigators:
                if p.name == self.principal_investigator:
                    break
            else:
                self._principal_investigators.append(PISpec(name=self.principal_investigator))
                self._backup()

    @cached_property
    def _get_project_enabled(self):
        return bool(self.principal_investigator)

    @cached_property
    def _get_sample_enabled(self):
        return bool(self.material) and bool(self.project) and bool(self.principal_investigator)

    @cached_property
    def _get_principal_investigators(self):
        with self.dvc.session_ctx():
            return self.dvc.get_principal_investigator_names()

    @cached_property
    def _get_materials(self):
        with self.dvc.session_ctx():
            ms = self.dvc.get_material_names()
            return ms

    @cached_property
    def _get_projects(self):
        with self.dvc.session_ctx():
            ps = self.dvc.get_project_names()
            return ps

    @cached_property
    def _get_grainsizes(self):
        with self.dvc.session_ctx():
            gs = [''] + self.dvc.get_grainsizes()
            return gs

# ============= EOF =============================================
