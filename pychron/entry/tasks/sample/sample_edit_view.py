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
import re

from traits.api import HasTraits, Instance, List, Str, Long
from traitsui.api import View, UItem, Item, VGroup, TableEditor, EnumEditor, Controller
from traitsui.menu import Action
from traitsui.table_column import ObjectColumn

EN = re.compile(r'(?P<a>\w*) \((?P<b>\w+, {0,1}\w+)\)')


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

    _projects = List
    _materials = List

    def __init__(self, rec, *args, **kw):
        super(SampleEditItem, self).__init__(*args, **kw)
        self.name = self._name = rec.name
        self.id = rec.id
        self.note = self._note = rec.note or ''

        if rec.project:
            self.project = self._project = rec.project.pname
        if rec.material:
            self.material = self._material = rec.material.gname

    @property
    def altered(self):
        attrs = 'name', 'project', 'material', 'note'
        return any((getattr(self, attr) != getattr(self, '_{}'.format(attr)) for attr in attrs))

    @property
    def project_pi(self):
        proj, pi = extract_names(self.project)
        return proj, pi


class SampleEditModel(HasTraits):
    sample = Str
    samples = List
    _materials = List
    _projects = List

    def init(self):
        self.dvc.create_session()
        self._projects = self.dvc.get_project_pnames()
        self._materials = self.dvc.get_material_gnames()

    def closed(self):
        self.dvc.close_session()

    def save(self):
        db = self.dvc
        for si in self.samples:
            if si.altered:
                dbsam = db.get_sample_id(si.id)
                dbsam.name = si.name
                dbsam.note = si.note

                dbproj = db.get_project(*extract_names(si.project))
                if dbproj:
                    dbsam.projectID = dbproj.id

                dbmat = db.get_material(*extract_names(si.material))
                # print dbmat, extract_names(si.material)
                if dbmat:
                    dbsam.materialID = dbmat.id
            db.commit()

    # handlers
    def _sample_changed(self):
        sams = []
        if len(self.sample) > 2:
            sams = self.dvc.get_samples_by_name(self.sample)
            sams = [SampleEditItem(si, _projects=self._projects,
                                   _materials=self._materials) for si in sams]

        self.samples = sams


class SampleEditView(Controller):
    dvc = Instance('pychron.dvc.dvc.DVC')

    def closed(self, info, is_ok):
        self.model.closed()

    def save(self, info):
        self.model.save()

    def traits_view(self):
        vv = View(VGroup(Item('name', label='Sample Name'),
                         Item('project', editor=EnumEditor(name='_projects')),
                         Item('material', editor=EnumEditor(name='_materials')),
                         VGroup(UItem('note', style='custom'), show_border=True, label='Note')))

        cols = [ObjectColumn(name='id', editable=False, text_font='arial 10'),
                ObjectColumn(name='name', editable=False, text_font='arial 10'),
                ObjectColumn(name='project', editable=False, text_font='arial 10'),
                ObjectColumn(name='material', editable=False, text_font='arial 10'),
                ObjectColumn(name='note', editable=False, text_font='arial 10')]

        a = UItem('sample')
        b = UItem('samples', editor=TableEditor(columns=cols,
                                                orientation='vertical',
                                                edit_view=vv))
        v = View(VGroup(a, b),
                 kind='livemodal',
                 width=500,
                 height=400,
                 buttons=[SaveAction(), ],
                 title='Edit Sample',
                 resizable=True)
        return v

# ============= EOF =============================================
