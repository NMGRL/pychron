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

from traits.api import Str

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.core.helpers.filetools import add_extension
from pychron.pipeline.nodes.base import BaseNode


class PersistNode(BaseNode):
    pass


class FileNode(PersistNode):
    root = Str
    extension = ''


class PDFNode(FileNode):
    extension = '.pdf'


class PDFFigureNode(PDFNode):
    name = 'PDF Figure'

    def _generate_path(self, ei):
        name = ei.name.replace(' ', '_')
        return os.path.join(self.root, add_extension(name, self.extension))

    def run(self, state):
        for ei in state.editors:
            if hasattr(ei, 'save_file'):
                ei.save_file(self._generate_path(ei))


# ============= EOF =============================================



