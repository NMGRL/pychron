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
from uncertainties import ufloat
from pychron.core.helpers.filetools import add_extension, unique_path2, view_file
from pychron.core.progress import progress_iterator
from pychron.paths import paths
from pychron.pipeline.nodes.base import BaseNode
from pychron.pipeline.nodes.persist_options import InterpretedAgePersistOptions, InterpretedAgePersistOptionsView


class PersistNode(BaseNode):
    def configure(self, **kw):
        return True


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
    commit_tag = Str
    modifier = Str
    # def __init__(self, *args, **kwargs):
    #     super(DVCPersistNode, self).__init__(*args, **kwargs)

    def _persist(self, state, msg):
        modp = self.dvc.update_analyses(state.unknowns,
                                        self.modifier,
                                        '<{}> {}'.format(self.commit_tag, msg))
        if modp:
            state.modified = True
            state.modified_projects = state.modified_projects.union(modp)


class IsotopeEvolutionPersistNode(DVCPersistNode):
    name = 'Save Iso Evo'
    commit_tag = 'ISOEVO'
    modifier = 'intercepts'

    def run(self, state):
        if not state.saveable_keys:
            return

        wrapper = lambda x, prog, i, n: self._save_fit(x, prog, i, n, state.saveable_keys)
        progress_iterator(state.unknowns, wrapper, threshold=1)
        # for ai in state.unknowns:
        #     self.dvc.save_fits(ai, state.saveable_keys)

        msg = self.commit_message
        if not msg:
            f = ','.join('{}({})'.format(x, y) for x, y in zip(state.saveable_keys, state.saveable_fits))
            msg = 'fits={}'.format(f)

        self._persist(state, msg)

    def _save_fit(self, x, prog, i, n, keys):
        if prog:
            prog.change_message('Save Fits {} {}/{}'.format(x.record_id, i, n))

        self.dvc.save_fits(x, keys)


class BlanksPersistNode(DVCPersistNode):
    name = 'Save Blanks'
    commit_tag = 'BLANKS'
    modifier = 'blanks'

    def run(self, state):
        # if not state.user_review:
        # for ai in state.unknowns:
        #     self.dvc.save_blanks(ai, state.saveable_keys, state.references)
        wrapper = lambda x, prog, i, n: self._save_blanks(x, prog, i, n,
                                                          state.saveable_keys, state.references)
        progress_iterator(state.unknowns, wrapper, threshold=1)
        msg = self.commit_message
        if not msg:
            f = ','.join('{}({})'.format(x, y) for x, y in zip(state.saveable_keys, state.saveable_fits))
            msg = 'auto update blanks, fits={}'.format(f)

        self._persist(state, msg)

    def _save_blanks(self, ai, prog, i, n, saveable_keys, references):
        if prog:
            prog.change_message('Save Blanks {} {}/{}'.format(ai.record_id, i, n))
        # print 'sssss', saveable_keys
        self.dvc.save_blanks(ai, saveable_keys, references)


class ICFactorPersistNode(DVCPersistNode):
    name = 'Save ICFactor'
    commit_tag = 'ICFactor'
    modifier = 'icfactors'

    def run(self, state):
        wrapper = lambda ai, prog, i, n: self._save_icfactors(ai, prog, i, n,
                                                              state.saveable_keys,
                                                              state.saveable_fits,
                                                              state.references)
        progress_iterator(state.unknowns, wrapper, threshold=1)

        # for ai in state.unknowns:
        #     self.dvc.save_icfactors(ai, state.saveable_keys,
        #                             state.saveable_fits,
        #                             state.references)

        msg = self.commit_message
        if not msg:
            f = ','.join('{}({})'.format(x, y) for x, y in zip(state.saveable_keys, state.saveable_fits))
            msg = 'auto update ic_factors, fits={}'.format(f)

        self._persist(state, msg)

    def _save_icfactors(self, ai, prog, i, n, saveable_keys, saveable_fits, reference):
        if prog:
            prog.change_message('Save IC Factor for {} {}/{}'.format(ai.record_id, i, n))

        self.dvc.save_icfactors(ai, saveable_keys, saveable_fits, reference)


class FluxPersistNode(DVCPersistNode):
    name = 'Save Flux'
    commit_tag = 'FLUX'

    def run(self, state):
        if state.saveable_irradiation_positions:
            xs = [x for x in state.saveable_irradiation_positions if x.save]
            if xs:
                progress_iterator(xs,
                                  lambda *args: self._save_j(state, *args),
                                  threshold=1)

                p = self.dvc.meta_repo.get_level_path(state.irradiation, state.level)
                self.dvc.meta_repo.add(p)
                self.dvc.meta_commit('fit flux for {}'.format(state.irradiation, state.level))

    def _save_j(self, state, irp, prog, i, n):
        if prog:
            prog.change_message('Save J for {} {}/{}'.format(irp.identifier, i, n))

        decay = state.decay_constants
        self.dvc.save_j(irp.irradiation, irp.level, irp.hole_id, irp.identifier,
                        irp.j, irp.jerr, decay,
                        analyses=irp.analyses,
                        add=False)

        j = ufloat(irp.j, irp.jerr, tag='j')
        for i in state.unknowns:
            if i.identifier == irp.identifier:
                i.j = j
                i.arar_constants.lambda_k = decay['lambda_k_total']
                i.recalculate_age()


class TablePersistNode(FileNode):
    pass


class XLSTablePersistNode(TablePersistNode):
    name = 'Save Excel Table'

    def run(self, state):
        from pychron.pipeline.editors.arar_table_editor import ArArTableEditor

        for editor in state.editors:
            if isinstance(editor, ArArTableEditor):
                basename = 'test_xls_table'
                path, _ = unique_path2(paths.data_dir, basename, extension='.xls')
                editor.make_xls_table('FooBar', path)
                view_file(path)


class InterpretedAgeTablePersistNode(BaseNode):
    name = 'Save IA Table'
    options_klass = InterpretedAgePersistOptionsView

    def _options_factory(self):
        opt = InterpretedAgePersistOptions(name='foo')
        return self.options_klass(model=opt)

    def run(self, state):
        from pychron.pipeline.editors.interpreted_age_table_editor import InterpretedAgeTableEditor
        for editor in state.editors:
            if isinstance(editor, InterpretedAgeTableEditor):
                opt = self.options.model
                if opt.extension == 'xls':
                    editor.make_xls_table(opt)
                    view_file(opt.path)
# ============= EOF =============================================
