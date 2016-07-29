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
from traits.api import HasTraits, Str, Any, Property, cached_property
from traitsui.api import View, UItem, Item, HGroup, VGroup, EnumEditor, TabularEditor

# ============= standard library imports ========================
# ============= local library imports  ==========================
from traitsui.tabular_adapter import TabularAdapter

from pychron.core.ui.combobox_editor import ComboboxEditor


class SessionAdapter(TabularAdapter):
    columns = [('Worker', 'worker_name'), ('Session', 'name'), ('Date', 'start_date')]


class SampleLocator(HasTraits):
    principal_investigator = Str
    principal_investigators = Property

    project = Str
    projects = Property(depends_on='principal_investigator')

    sample = Str
    samples = Property(depends_on='project')

    session = Any
    sessions = Property(depends_on='sample')

    @cached_property
    def _get_principal_investigators(self):
        return self.dvc.get_principal_investigator_names()

    @cached_property
    def _get_sessions(self):
        if self.sample:
            with self.dvc.session_ctx() as sess:
                ss = self.dvc.get_sample_prep_sessions(self.sample)
                sess.expunge_all()
                return ss
        else:
            return []

    @cached_property
    def _get_projects(self):
        if self.principal_investigator:
            with self.dvc.session_ctx():
                return [p.name for p in self.dvc.get_projects(self.principal_investigator)]
        else:
            return []

    @cached_property
    def _get_samples(self):
        if self.project:
            with self.dvc.session_ctx():
                return [si.name for si in self.dvc.get_samples(project=self.project)]
        else:
            return []

    def traits_view(self):
        agrp = HGroup(Item('principal_investigator', label='PI',
                           editor=EnumEditor(name='principal_investigators')),
                      Item('project', label='Project',
                           editor=ComboboxEditor(name='projects')),
                      Item('sample', label='Sample',
                           editor=ComboboxEditor(name='samples')))
        bgrp = VGroup(UItem('sessions', editor=TabularEditor(adapter=SessionAdapter(),
                                                             selected='session')))
        v = View(VGroup(agrp,
                        bgrp),
                 buttons=['OK', 'Cancel'],
                 kind='livemodal',
                 resizable=True,
                 title='Locate Sample')
        return v

# ============= EOF =============================================
