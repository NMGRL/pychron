# ===============================================================================
# Copyright 2015 Jake Ross
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

from traits.api import HasTraits, Str, File
from traitsui.api import View, Item, Controller

# ============= standard library imports ========================
# ============= local library imports  ==========================
from traitsui.menu import Action
from pychron.core.helpers.filetools import unique_path2
from pychron.core.ui.combobox_editor import ComboboxEditor
from pychron.paths import paths


class SaveFigureModel(HasTraits):
    root_directory = Str
    name = Str
    path = File

    def __init__(self, analyses):
        self.experiment_identifiers = tuple({ai.experiment_identifier for ai in analyses})
        self.root_directory = self.experiment_identifiers[0]

        identifiers = tuple({ai.identifier for ai in analyses})
        self.name = '_'.join(identifiers)

    def prepare_path(self, make=False):
        return self._prepare_path(make=make)

    def _prepare_path(self, make=False):
        root = os.path.join(paths.figure_dir, self.root_directory)
        if make and not os.path.isdir(root):
            os.mkdir(root)

        path, cnt = unique_path2(root, self.name, extension='.pdf')
        return path


FinderAction = Action(name='Finder', action='use_finder')


class SaveFigureView(Controller):
    def object_name_changed(self, info):
        self._set_path()

    def object_root_directory_changed(self, info):
        self._set_path()

    def _set_path(self):
        path = self.model.prepare_path()
        self.model.path = path

    def traits_view(self):
        v = View(Item('root_directory', label='Directory',
                      editor=ComboboxEditor(name='experiment_identifiers')),
                 Item('name'),
                 Item('path'),
                 buttons=['OK', 'Cancel'],
                 title='Save PDF Dialog',
                 width=400,
                 kind='livemodal')
        return v


if __name__ == '__main__':
    import random

    paths.build('_dev')


    class A(object):
        def __init__(self):
            self.experiment_identifier = random.choice(['Foo', 'Bar', 'Bat'])
            self.identifier = '1000'


    ans = [A() for i in range(5)]
    sfm = SaveFigureModel(ans)
    sfv = SaveFigureView(model=sfm)
    sfv.configure_traits()

# ============= EOF =============================================
