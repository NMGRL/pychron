#===============================================================================
# Copyright 2013 Jake Ross
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#===============================================================================

#============= enthought library imports =======================

#============= standard library imports ========================
import os
#============= local library imports  ==========================
#from pychron.experiment.easy_parser import EasyParser
from pychron.core.helpers.filetools import unique_path
from pychron.core.helpers.iterfuncs import partition
from pychron.paths import r_mkdir
from pychron.processing.easy.base_easy import BaseEasy
from pychron.processing.tasks.figures.editors.ideogram_editor import IdeogramEditor
from pychron.processing.tasks.figures.editors.spectrum_editor import SpectrumEditor


class EasyFigures(BaseEasy):
    fusion_editor_klass = IdeogramEditor
    step_heat_editor_klass = SpectrumEditor

    _fusion_editor = None
    _step_heat_editor = None

    _tag = 'Figure'

    _save_db_figure=False

    def _make(self, ep):
        #make a figure for each labnumber

        doc = ep.doc('figures')

        self._save_db_figure=doc['save_db_figure']
        self._save_interpreted=doc['save_interpreted']

        projects = doc['projects']
        identifiers = doc.get('identifiers')

        db = self.db
        with db.session_ctx():
            if identifiers:
                lns=[db.get_labnumber(li) for li in identifiers]

            else:
                lns = [ln for proj in projects
                       for si in db.get_samples(project=proj)
                       for ln in si.labnumbers]
            self._make_labnumbers(doc, lns)

    def _make_labnumbers(self, doc, lns):
        root=doc['root']
        options = doc['options']
        n = len(lns) + sum([len(li.analyses) for li in lns])
        prog = self.open_progress(n, close_at_end=False)

        for li in lns:
            self._make_labnumber(li, root, options, prog)

        prog.close()
        self.info('easy make finished')

    def _make_labnumber(self, li, root, options, prog):
        #make dir for labnumber
        ident = li.identifier
        ln_root = os.path.join(root, ident)
        r_mkdir(ln_root)

        prog.change_message('Making {} for {}'.format(self._tag, ident))

        #group by stepheat vs fusion
        pred = lambda x: bool(x.step)
        ans = sorted(li.analyses, key=pred)
        stepheat, fusion = map(list, partition(ans, pred))

        apred = lambda x: x.aliquot
        stepheat = sorted(stepheat, key=apred)
        if stepheat:
            self._make_editor(stepheat, 'step_heat', options, prog, ln_root, li)
        if fusion:
            self._make_editor(fusion, 'fusion', options, prog, ln_root, li)

    def _make_editor(self, ans, editor_name, options, prog, ln_root, li):

        editor=getattr(self, '_{}_editor'.format(editor_name))
        if editor is None:
            klass=getattr(self, '{}_editor_klass'.format(editor_name))
            editor=klass(processor=self)
            editor.plotter_options_manager.set_plotter_options(options[editor_name])

        unks = self.make_analyses(ans, progress=prog)
        editor.set_items(unks)
        editor.rebuild()

        func=getattr(self, '_save_{}'.format(editor_name))
        func(editor, ln_root, li)
        setattr(self, '_{}_editor'.format(editor_name), editor)

    #save
    def _save_step_heat(self,editor, *args):
        self._save('{}_step_heat_figure', editor, *args)

        if self._save_interpreted:
            ias = editor.get_interpreted_ages()
            for ia in ias:
                if ia.plateau_age:
                    ia.preferred_age_kind = 'Plateau'
                else:
                    ia.preferred_age_kind = 'Integrated'

            editor.add_interpreted_ages(ias)

    def _save_fusion(self, *args):
        self._save('{}_fusion_figure', *args)

    def _save(self, tag, editor, root, ln):
        p, _ = unique_path(root, tag.format(ln.identifier), extension='.pdf')
        editor.save_file(p)
        if self._save_db_figure:
            editor.save_figure('EasyFigure {}'.format(ln.identifier),
                               ln.sample.project.name, [ln.sample.name])


#============= EOF =============================================
