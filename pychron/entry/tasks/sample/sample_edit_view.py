# ===============================================================================
# Copyright 2016 ross
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
import re

from traits.api import HasTraits, Instance, List, Str, Long, Float, BaseFloat
from traitsui.api import View, UItem, Item, VGroup, TableEditor, EnumEditor, Controller, HGroup
from traitsui.menu import Action
from traitsui.table_column import ObjectColumn



EN = re.compile(r'(?P<a>[\w\W]+) \((?P<b>[\w\W]+, ?[\w\W]+)\)')

SAMPLE_ATTRS = ('lat', 'lon', 'igsn', 'storage_location',
                'lithology', 'location', 'approximate_age', 'elevation',
                'note')


class LatFloat(BaseFloat):
    def validate(self, obj, name, value):
        if not isinstance(value, (float, int)):
            return self.error(obj, name, value)
        else:
            if value > 90 or value < -90:
                return self.error(obj, name, value)
            else:
                return value


class LonFloat(BaseFloat):
    def validate(self, obj, name, value):
        if not isinstance(value, (float, int)):
            return self.error(obj, name, value)
        else:
            if value > 180 or value < -180:
                return self.error(obj, name, value)
            else:
                return value

def extract_names(s):
    a = s
    b = None
    mat = EN.match(s)
    if mat:
        a = mat.group('a')
        b = mat.group('b')

    return a, b


class SaveAction(Action):
    name = 'Save'
    action = 'save'


class SampleEditItem(HasTraits):
    name = Str
    project = Str
    material = Str
    grainsize = Str
    id = Long
    note = Str

    lat = LatFloat
    lon = LonFloat
    igsn = Str
    lithology = Str
    location = Str
    storage_location = Str
    approximate_age = Float
    elevation = Float

    _projects = List
    _materials = List

    _project = Str
    _material = Str
    _note = Str
    _lat = LatFloat
    _lon = LonFloat
    _igsn = Str
    _lithology = Str
    _location = Str
    _storage_location = Str
    _approximate_age = Float
    _elevation = Float

    def __init__(self, rec=None, *args, **kw):
        super(SampleEditItem, self).__init__(*args, **kw)
        if rec:
            self.id = rec.id

            self.name = self._name = rec.name
            # self.note = self._note = rec.note or ''

            self.project = self._project = rec.project.pname if rec.project else ''
            self.material = self._material = rec.material.gname if rec.material else ''
            # self.project_name = rec.project.name
            # self.principal_investigator = rec.project.principal_investigator
            for attr in SAMPLE_ATTRS:
                v = getattr(rec, attr)
                if v is not None:
                    try:
                        setattr(self, attr, v)
                        setattr(self, '_{}'.format(attr), v)
                    except ValueError:
                        pass

    @property
    def altered(self):
        attrs = ('name', 'project', 'material') + SAMPLE_ATTRS
        try:
            return any((getattr(self, attr) != getattr(self, '_{}'.format(attr)) for attr in attrs))
        except AttributeError:
            return False

    @property
    def project_pi(self):
        proj, pi = extract_names(self.project)
        return proj, pi

    def traits_view(self):
        vv = View(VGroup(Item('name', label='Sample Name'),
                         Item('project', editor=EnumEditor(name='_projects')),
                         Item('material', editor=EnumEditor(name='_materials')),
                         HGroup(VGroup(Item('lat', label='Latitude'),
                                       Item('lon', label='Longitude'),
                                       Item('location'),
                                       Item('elevation'),
                                       label='Location', show_border=True),
                                VGroup(Item('lithology'),
                                       Item('approximate_age', label='Approx. Age (Ma)'),
                                       Item('storage_location'),
                                       show_border=True)),
                         VGroup(UItem('note', style='custom'), show_border=True, label='Note')))
        return vv


class SampleEditModel(HasTraits):
    dvc = Instance('pychron.dvc.dvc.DVC')
    sample = Str
    samples = List
    _materials = List
    _projects = List
    sample_item = Instance(SampleEditItem, ())

    def set_sample(self, rec):
        self.sample_item = SampleEditItem(rec, _projects=self._projects, _materials=self._materials)

    def init(self):
        self._projects = self.dvc.get_project_pnames()
        self._materials = self.dvc.get_material_gnames()

    def save(self):
        db = self.dvc
        # for si in self.samples:
        si = self.sample_item
        if si.altered:
            dbsam = db.get_sample_id(si.id)
            dbsam.name = si.name
            # dbsam.note = si.note
            # dbsam.lat = si.lat
            for attr in SAMPLE_ATTRS:
                setattr(dbsam, attr, getattr(si, attr))

            print('a', si.project_pi, 'b', si.project)
            dbproj = db.get_project(*si.project_pi)
            if dbproj:
                dbsam.projectID = dbproj.id

            dbmat = db.get_material(*extract_names(si.material))
            # print dbmat, extract_names(si.material)
            if dbmat:
                dbsam.materialID = dbmat.id
            db.commit()
            return True

    # handlers
    def _sample_changed(self):
        # sams = []
        if len(self.sample) > 2:
            sams = self.dvc.get_samples_by_name(self.sample)
            # sams = [SampleEditItem(si, _projects=self._projects,
            #                        _materials=self._materials) for si in sams]
            self.sample_item = SampleEditItem(sams[0], _projects=self._projects, _materials=self._materials)
        # self.samples = sams

    def traits_view(self):
        return View(UItem('sample_item', style='custom'))

# ============= EOF =============================================
