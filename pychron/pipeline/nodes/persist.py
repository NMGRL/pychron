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
from traits.api import Str, Instance
from traitsui.api import Item
# ============= standard library imports ========================
import os
# ============= local library imports  ==========================
from traitsui.editors import DirectoryEditor
from pychron.core.helpers.filetools import add_extension
from pychron.paths import paths
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

    def traits_view(self):

        return self._view_factory(Item('root', editor=DirectoryEditor(root_path=paths.data_dir)),
                                  width=500)
        return v

    def _generate_path(self, ei):
        name = ei.name.replace(' ', '_')
        return os.path.join(self.root, add_extension(name, self.extension))

    def run(self, state):
        for ei in state.editors:
            if hasattr(ei, 'save_file'):
                print 'save file to', self._generate_path(ei)
                ei.save_file(self._generate_path(ei))


class DVCPersistNode(PersistNode):
    dvc = Instance('pychron.dvc.dvc.DVC')
    commit_message = Str

    def _persist(self, state, msg):
        modp = self.dvc.update_analyses(state.unknowns, msg)
        if modp:
            state.modified = True
            state.modified_projects = state.modified_projects.union(modp)


class IsotopeEvolutionPersistNode(DVCPersistNode):
    name = 'Save Iso Evo'

    def configure(self):
        return True

    def run(self, state):
        for ai in state.unknowns:
            self.dvc.save_fits(ai, state.saveable_keys)

        msg = self.commit_message
        if not msg:
            f = ','.join('{}({})'.format(x, y) for x, y in zip(state.saveable_keys, state.saveable_fits))
            msg = 'auto update iso evo, fits={}'.format(f)

        self._persist(state, msg)


class BlanksPersistNode(DVCPersistNode):
    name = 'Save Blanks'

    def configure(self):
        return True

    def run(self, state):
        # if not state.user_review:
        for ai in state.unknowns:
            self.dvc.save_blanks(ai, state.saveable_keys, state.references)

        msg = self.commit_message
        if not msg:
            f = ','.join('{}({})'.format(x, y) for x, y in zip(state.saveable_keys, state.saveable_fits))
            msg = 'auto update blanks, fits={}'.format(f)

        self._persist(state, msg)


class ICFactorPersistNode(DVCPersistNode):
    name = 'Save ICFactor'

    def configure(self):
        return True

    def run(self, state):
        for ai in state.unknowns:
            self.dvc.save_icfactors(ai, state.saveable_keys,
                                    state.saveable_fits,
                                    state.references)

        msg = self.commit_message
        if not msg:
            f = ','.join('{}({})'.format(x, y) for x, y in zip(state.saveable_keys, state.saveable_fits))
            msg = 'auto update ic_factors, fits={}'.format(f)

        self._persist(state, msg)


class FluxPersistNode(DVCPersistNode):
    name = 'Save Flux'

    def run(self, state):
        pass
# ============= EOF =============================================
