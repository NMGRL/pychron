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

from __future__ import absolute_import
from __future__ import print_function

import os
import re

import yaml
# ============= enthought library imports =======================
from traits.api import HasTraits, Str, Bool, Property, Event, cached_property, \
    Button, String, Instance, List, Float, on_trait_change
from traitsui.api import View, UItem, Item, VGroup, HGroup

from pychron.core.pychron_traits import EmailStr
from pychron.dvc.dvc_irradiationable import DVCAble
from pychron.entry.tasks.sample.sample_edit_view import SampleEditModel, LatFloat, LonFloat, SAMPLE_ATTRS
from pychron.envisage.icon_button_editor import icon_button_editor
from pychron.paths import paths

PI_REGEX = re.compile(r'^[A-Z]+\w+(, ?[A-Z]{1})*$')
# MATERIAL_REGEX = re.compile(r'^[A-Z]+[\w%/\+-_]+$')
PROJECT_REGEX = re.compile(r'^[a-zA-Z]+[\-\d_\w]*$')


class RString(String):
    def validate(self, obj, name, value):
        if not self.regex.match(value):
            return self.error(obj, name, value)
        else:
            return value


PI_NAMES = ('NMGRL',)
if os.path.isfile(paths.valid_pi_names):
    with open(paths.valid_pi_names, 'r') as rf:
        PI_NAMES = yaml.load(rf)


class PIStr(String):
    def validate(self, obj, name, value):
        if not PI_REGEX.match(value) and value not in PI_NAMES:
            return self.error(obj, name, value)
        else:
            return value


# class MaterialStr(RString):
#     regex = MATERIAL_REGEX



class ProjectStr(String):
    regex = PROJECT_REGEX


class Spec(HasTraits):
    name = Str
    added = Bool


class PISpec(Spec):
    affiliation = Str
    email = EmailStr

    def todump(self):
        return {'name': str(self.name),
                'affiliation': str(self.affiliation),
                'email': str(self.email)}

    @classmethod
    def fromdump(cls, d):
        obj = cls()
        obj.name = d['name']
        obj.email = d.get('email', '')
        obj.affiliation = d.get('affiliation', '')
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
    lab_contact = Str
    comment = Str
    institution = Str

    @property
    def optionals(self):
        return {'lab_contact': self.lab_contact, 'comment': self.comment, 'institution': self.institution}

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
    note = Str
    lat = Float
    lon = Float
    igsn = Str
    storage_location = Str
    lithology = Str
    location = Str
    approximate_age = Float
    elevation = Float

    def todump(self):
        d = {'name': str(self.name), 'project': self.project.todump(),
             'material': self.material.todump()}
        for attr in SAMPLE_ATTRS:
            d[attr] = getattr(self, attr)

    @classmethod
    def fromdump(cls, d, pps, ms):
        obj = cls()
        for attr in SAMPLE_ATTRS:
            try:
                setattr(obj, attr, d[attr])
            except KeyError:
                pass

        project = d['project']
        pname = project['name']
        piname = project['principal_investigator']['name']
        for pp in pps:
            # print(pname, pp.name, piname, pp.principal_investigator.name)
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
    email = EmailStr
    affiliation = Str

    refresh_pis = Event

    project = ProjectStr(enter_set=True, auto_set=False)
    projects = Property(depends_on='refresh_projects')
    refresh_projects = Event

    material = Str
    materials = Property(depends_on='refresh_materials')
    refresh_materials = Event
    grainsize = Str
    grainsizes = Property(depends_on='refresh_grainsizes')
    refresh_grainsizes = Event

    sample = Str
    note = Str
    lat = LatFloat
    lon = LonFloat
    igsn = Str
    lithology = Str
    location = Str
    storage_location = Str
    approximate_age = Float
    elevation = Float

    clear_sample_attributes_button = Button
    configure_sample_button = Button
    configure_pi_button = Button
    add_principal_investigator_button = Button
    add_project_button = Button
    add_sample_button = Button
    add_sample_enabled = Property(depends_on='sample, _add_sample_enabled')
    _add_sample_enabled = Bool

    add_button = Button
    add_material_button = Button
    generate_project_button = Button('Generate Name')
    set_optionals_button = Button('Set Optionals')

    project_comment = Str
    project_institution = Str
    project_lab_contact = Str
    lab_contacts = List

    lock_project_comment = Bool
    lock_project_institution = Bool
    lock_project_lab_contact = Bool

    project_enabled = Property(depends_on='principal_investigator')
    sample_enabled = Property(depends_on='principal_investigator, project, material')

    refresh_table = Event

    db_samples = List
    sample_filter = String(enter_set=True, auto_set=False)
    sample_filter_attr = Str('name')
    sample_filter_attrs = List(('name', 'project', 'material', 'principal_investigator')+SAMPLE_ATTRS)
    selected_db_samples = List

    _samples = List
    _projects = List
    _materials = List
    _principal_investigators = List
    _default_project_count = 0

    selected_samples = List
    selected_projects = List
    selected_principal_investigators = List
    selected_materials = List

    sample_edit_model = Instance(SampleEditModel, ())

    def activated(self):
        self.refresh_pis = True
        self.refresh_materials = True
        self.refresh_projects = True
        self.refresh_grainsizes = True
        self.dvc.create_session()
        self.sample_edit_model.dvc = self.dvc

    def prepare_destroy(self):
        self._backup()
        self.dvc.close_session()

    def clear(self):
        if self.selected_principal_investigators:
            for p in self.selected_principal_investigators:
                if not p.added:
                    self._principal_investigators.remove(p)

            self._projects = [p for p in self._projects
                              if p.principal_investigator not in self.selected_principal_investigators]
            self._samples = [s for s in self._samples
                             if s.project.principal_investigator not in self.selected_principal_investigators]

            self.selected_principal_investigators = []

        if self.selected_projects:
            for p in self.selected_projects:
                if not p.added:
                    try:
                        self._projects.remove(p)
                    except ValueError:
                        pass

            self._samples = [s for s in self._samples if s.project not in self.selected_projects]
            self.selected_projects = []

        if self.selected_materials:
            for mi in self.selected_materials:
                if not mi.added:
                    try:
                        self._materials.remove(mi)
                    except ValueError:
                        pass

            self._samples = [s for s in self._samples if s.material not in self.selected_materials]
            self.selected_materials = []

        if self.selected_samples:
            for ri in self.selected_samples:
                if not ri.added:
                    try:
                        self._samples.remove(ri)
                    except ValueError:
                        pass

            self.selected_samples = []

    def save(self):
        msg = None
        if not self.sample_edit_model.save():
            self._backup()
            if self._save():
                msg = 'Samples added to database'
        else:
            # refresh samples in display table
            self._handle_sample_filter()

            msg = 'Changes saved to database'

        if msg:
            self.information_dialog(msg)

    def load(self, p):
        with open(p, 'r') as rfile:
            obj = yaml.load(rfile)
            self._principal_investigators = ps = [PISpec.fromdump(p) for p in obj['principal_investigators'] if
                                                  p is not None]
            self._materials = ms = [MaterialSpec.fromdump(p) for p in obj['materials'] if p is not None]

            self._projects = pps = [ProjectSpec.fromdump(p, ps) for p in obj['projects'] if p is not None]
            self._samples = [SampleSpec.fromdump(p, pps, ms) for p in obj['samples'] if p is not None]

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
    def _selected_db_samples_changed(self, new):
        if new:
            self.sample_edit_model.init()
            self.sample_edit_model.set_sample(new[0])

    @on_trait_change('sample_filter_attr, sample_filter')
    def _handle_sample_filter(self):
        if self.sample_filter and self.sample_filter_attr:
            sams = self.dvc.get_samples_filter(self.sample_filter_attr, self.sample_filter)
            self.db_samples = sams

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
        if not any((getattr(self, attr) for attr in ('_principal_investigators', '_materials', '_projects',
                                                     '_samples'))):
            return

        self.debug('saving sample info')
        dvc = self.dvc
        with dvc.session_ctx(use_parent_session=False):
            for p in self._principal_investigators:
                if dvc.add_principal_investigator(p.name, email=p.email, affiliation=p.affiliation):
                    p.added = True
                    dvc.commit()

        for p in self._projects:
            with dvc.session_ctx(use_parent_session=False):

                if p.name.startswith('?'):
                    if dvc.add_project(p.name, p.principal_investigator.name,
                                       **p.optionals):
                        dbproject = dvc.get_project(p.name, p.principal_investigator.name)
                        p.added = True
                        dvc.commit()

                        dbproject.name = p.name = '{}{}'.format(p.name[1:-2], dbproject.id)
                        if self.project.startswith('?'):
                            self.project = p.name

                        dvc.commit()

                else:
                    if dvc.add_project(p.name, p.principal_investigator.name, **p.optionals):
                        p.added = True
                        dvc.commit()

        for m in self._materials:
            with dvc.session_ctx(use_parent_session=False):
                if dvc.add_material(m.name, m.grainsize or None):
                    m.added = True
                    dvc.commit()

        for s in self._samples:
            with dvc.session_ctx(use_parent_session=False):
                if not s.name:
                    self.warning_dialog('A Sample name is required')
                    continue
                if (s.project and not s.project.name) or not s.project:
                    self.warning_dialog('A project name is required. Skipping {}'.format(s.name))
                if (s.material and not s.material.name) or not s.material:
                    self.warning_dialog('A material is required. Skipping {}'.format(s.name))

                if dvc.add_sample(s.name, s.project.name, s.project.principal_investigator.name,
                                  s.material.name,
                                  s.material.grainsize or None,
                                  igsn=s.igsn,
                                  storage_location=s.storage_location,
                                  lithology=s.lithology,
                                  location=s.location,
                                  approximate_age=s.approximate_age,
                                  elevation=s.elevation,
                                  lat=s.lat, lon=s.lon,
                                  note=s.note):
                    s.added = True
                    dvc.commit()

        self.refresh_table = True
        return True

    def _principal_investigator_factory(self):
        p = PISpec(name=self.principal_investigator,
                   email=self.email,
                   affiliation=self.affiliation)

        self._principal_investigators.append(p)
        return p

    def _get_principal_investigator_spec(self):
        for p in self._principal_investigators:
            if p.name == self.principal_investigator:
                return p
        else:
            p = self._principal_investigator_factory()
            return p

    def _get_project_spec(self):
        if self.project:
            pspec = self._get_principal_investigator_spec()
            for p in self._projects:
                if p.name == self.project and p.principal_investigator.name == pspec.name:
                    return p
            else:
                p = self._new_project_spec(pspec)
                return p

    def _new_project_spec(self, principal_investigator_spec):
        project_spec = ProjectSpec(name=self.project,
                                   principal_investigator=principal_investigator_spec)

        for attr in ('lab_contact', 'comment', 'institution'):
            name = 'project_{}'.format(attr)
            setattr(project_spec, attr, getattr(self, name))
            if not getattr(self, 'lock_{}'.format(name)):
                setattr(self, name, '')

        self._projects.append(project_spec)

        return project_spec

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
    def _clear_sample_attributes_button_fired(self):
        self.storage_location = ''
        self.lithology = ''
        self.lat = 0
        self.lon = 0
        self.location = ''
        self.elevation = 0
        self.igsn = ''
        self.note = ''
        self.approximate_age = 0

    def _configure_pi_button_fired(self):
        v = View(VGroup(VGroup(UItem('principal_investigator'),
                               label='Name', show_border=True),
                        VGroup(Item('affiliation', label='Affiliation'),
                               Item('email', label='Email'),
                               label='Optional', show_border=True)),
                 kind='livemodal', title='Set Principal Investigator Attributes',
                 buttons=['OK', 'Cancel'])
        self.edit_traits(view=v)

    def _configure_sample_button_fired(self):
        v = View(VGroup(HGroup(icon_button_editor('clear_sample_attributes_button', 'clear')),
                        VGroup(UItem('sample'),
                               label='Name', show_border=True),
                        VGroup(Item('lat', label='Latitude'),
                               Item('lon', label='Longitude'),
                               Item('location'),
                               Item('elevation'),
                               label='Location', show_border=True),
                        VGroup(Item('lithology'),
                               Item('approximate_age', label='Approx. Age (Ma)'),
                               Item('storage_location'),
                               show_border=True),
                        ),
                 kind='livemodal', title='Set Sample Attributes',
                 buttons=['OK', 'Cancel'])
        self.edit_traits(view=v)

    def _add_sample_button_fired(self):
        if self.sample:

            material_spec = self._get_material_spec()
            if not material_spec or not material_spec.name:
                self.information_dialog('Please enter a material for this sample')
                return

            project_spec = self._get_project_spec()
            if not project_spec or not project_spec.name:
                self.information_dialog('Please enter a project for this sample')
                return

            self._samples.append(SampleSpec(name=self.sample,
                                            lat=self.lat,
                                            lon=self.lon,
                                            igsn=self.igsn,
                                            note=self.note,
                                            project=project_spec,
                                            material=material_spec))
            self._backup()
            self._add_sample_enabled = False

    def _add_project_button_fired(self):
        if self.project:
            pispec = self._get_principal_investigator_spec()
            for p in self._projects:
                if p.name == self.project and p.principal_investigator.name == pispec.name:
                    break
            else:
                self._new_project_spec(pispec)
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
                self._principal_investigator_factory()
                self._backup()

    def _generate_project_button_fired(self):
        piname = self.principal_investigator
        if ',' in piname:
            piname = piname.split(',')[0]
        self.project = '?{}{:03n}'.format(piname, self._default_project_count)
        self._default_project_count += 1

    def _set_optionals_button_fired(self):
        self.lab_contacts = self.dvc.get_usernames()

        from pychron.entry.tasks.sample.project_optionals_view import ProjectOptionalsView
        v = ProjectOptionalsView(model=self)
        v.edit_traits()

    def _sample_changed(self):
        self._add_sample_enabled = True

    @cached_property
    def _get_project_enabled(self):
        return bool(self.principal_investigator)

    @cached_property
    def _get_add_sample_enabled(self):
        return bool(self.sample) and self._add_sample_enabled

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
