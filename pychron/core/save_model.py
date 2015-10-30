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
from pyface.constant import OK
from pyface.file_dialog import FileDialog
from traits.api import HasTraits, Str, Bool, Button
from traitsui.api import UItem, Item, HGroup, VGroup, spring, Controller, DirectoryEditor
# ============= standard library imports ========================
import os
# ============= local library imports  ==========================
from pychron.core.helpers.filetools import unique_path2, add_extension
from pychron.paths import paths


class SaveModel(HasTraits):
    root_directory = Str
    name = Str
    path = Str
    use_manual_path = Bool(False)
    extension = '.pdf'

    @property
    def default_root(self):
        return paths.figure_dir

    def dump(self):
        pass

    def prepare_path(self, make=False):
        if self.use_manual_path:
            return self.path
        else:
            return self._prepare_path(make=make)

    def _prepare_path(self, make=False):
        root = os.path.join(self.default_root, self.root_directory)
        if make and not os.path.isdir(root):
            os.mkdir(root)

        path, cnt = unique_path2(root, self.name, extension=self.extension)
        return path


class SaveController(Controller):
    use_finder_button = Button('Use Finder')

    def closed(self, info, is_ok):
        if is_ok:
            self.model.dump()

    def _use_finder_button_fired(self):
        dlg = FileDialog(action='save as')
        if dlg.open() == OK:
            self.model.use_manual_path = True
            self.model.path = add_extension(dlg.path, self.model.extension)

    def object_name_changed(self, info):
        self._set_path()

    def object_root_directory_changed(self, info):
        self._set_path()

    def _set_path(self):
        self.model.use_manual_path = False
        path = self.model.prepare_path()
        self.model.path = path

    def _get_root_item(self):
        return Item('root_directory',
                    label='Directory',
                    editor=DirectoryEditor())

    def _get_path_group(self, label='File', **kw):
        path_group = VGroup(self._get_root_item(),
                            Item('name'),
                            HGroup(UItem('controller.use_finder_button'), spring),
                            Item('path', style='readonly'),
                            label=label, **kw)
        return path_group

# ============= EOF =============================================
