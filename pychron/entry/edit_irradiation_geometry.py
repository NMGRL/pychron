# ===============================================================================
# Copyright 2019 ross
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
import os

from traits.api import HasTraits, Str, Instance, List, Property, Button
from traitsui.api import VGroup, UItem, HGroup, EnumEditor

from pychron.core.helpers.filetools import add_extension
from pychron.core.helpers.traitsui_shortcuts import okcancel_view
from pychron.dvc.dvc import DVC
from pychron.envisage.icon_button_editor import icon_button_editor
from pychron.paths import paths


class EditIrradiationGeometry(HasTraits):
    text = Str
    otext = Str
    changed = Property(depends='text')
    dvc = Instance(DVC)
    name = Str
    names = List

    save_button = Button

    def __init__(self, *args, **kw):
        super(EditIrradiationGeometry, self).__init__(*args, **kw)
        self.dvc.meta_pull()
        self.names = self.dvc.meta_repo.get_irradiation_holder_names()
        self.name = self.names[0]

    def _name_changed(self, new):
        if new:
            p = os.path.join(paths.meta_root, 'irradiation_holders', add_extension(new))
            with open(p, 'r') as rfile:
                self.text = rfile.read()
                self.otext = self.text

    def _save_button_fired(self):
        p = os.path.join(paths.meta_root, 'irradiation_holders', add_extension(self.name))
        with open(p, 'w') as wfile:
            wfile.write(self.text)

        self.dvc.meta_repo.add(p, commit=False)
        self.dvc.commit('updated {}'.format(self.name))
        self.dvc.meta_push()

    def _get_changed(self):
        return self.text != self.otext

    def traits_view(self):
        agrp = HGroup(UItem('name', editor=EnumEditor(name='names')),
                      icon_button_editor('save_button', 'save', enabled_when='changed'))
        tgrp = VGroup(UItem('text', style='custom'))
        grp = VGroup(agrp, tgrp)

        return okcancel_view(grp, width=400, height=600, title='Edit Irradiation Geometry')

# ============= EOF =============================================
