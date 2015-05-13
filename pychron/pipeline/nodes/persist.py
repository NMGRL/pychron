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
from traits.api import Str
from traitsui.api import View, Item
# ============= standard library imports ========================
import os
# ============= local library imports  ==========================
from traitsui.editors import DirectoryEditor
from pychron.core.helpers.filetools import add_extension
from pychron.paths import paths
from pychron.pipeline.nodes.base import BaseNode


class PersistNode(BaseNode):
    def configure(self):
        info = self.edit_traits()
        if info.result:
            return True


class FileNode(PersistNode):
    root = Str
    extension = ''


class PDFNode(FileNode):
    extension = '.pdf'


class PDFFigureNode(PDFNode):
    name = 'PDF Figure'

    def traits_view(self):
        v = View(Item('root', editor=DirectoryEditor(root_path=paths.data_dir)),
                 title='Configure {}'.format(self.name),
                 kind='livemodal',
                 width=500,
                 resizable=True,
                 buttons=['OK', 'Cancel'])
        return v

    def _generate_path(self, ei):
        name = ei.name.replace(' ', '_')
        return os.path.join(self.root, add_extension(name, self.extension))

    def run(self, state):
        for ei in state.editors:
            if hasattr(ei, 'save_file'):
                print 'save file to', self._generate_path(ei)
                ei.save_file(self._generate_path(ei))


# ============= EOF =============================================



