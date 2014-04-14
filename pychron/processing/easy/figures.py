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
from itertools import groupby
import os
#============= local library imports  ==========================
#from pychron.experiment.easy_parser import EasyParser
from pychron.core.helpers.filetools import unique_path
from pychron.core.helpers.iterfuncs import partition
from pychron.experiment.utilities.identifier import make_runid
from pychron.paths import r_mkdir
from pychron.processing.easy.base_easy import BaseEasy
from pychron.processing.tasks.figures.editors.ideogram_editor import IdeogramEditor
from pychron.processing.tasks.figures.editors.isochron_editor import InverseIsochronEditor
from pychron.processing.tasks.figures.editors.spectrum_editor import SpectrumEditor
from pychron.processing.utils.grouping import group_analyses_by_key


class EasyFigures(BaseEasy):
    fusion_editor_klass = IdeogramEditor
    step_heat_editor_klass = SpectrumEditor
    isochron_editor_klass = InverseIsochronEditor

    _fusion_editor = None
    _step_heat_editor = None
    _isochron_editor = None

    _tag = 'Figure'

    _save_db_figure = False

    def _make(self, ep):
        #make a figure for each labnumber

        doc = ep.doc('figures')

        self._save_db_figure = doc['save_db_figure']
        self._save_pdf_figure = doc['save_pdf_figure']
        self._save_interpreted = doc['save_interpreted']

        projects = doc['projects']
        identifiers = doc.get('identifiers')
        grouped_identifiers = doc.get('identifier_groups', None)
        levels = doc.get('levels')

        db = self.db
        with db.session_ctx():
            if levels:
                for li_str in levels:
                    irrad, level = li_str.split(' ')
                    dblevel = db.get_irradiation_level(irrad, level)
                    pos = [pp for pp in dblevel.positions if pp.labnumber]

                    lns = [pp.labnumber for pp in pos
                           if pp.labnumber.sample.project.name in projects]

                    ans = [ai for li in lns
                           for ai in li.analyses
                           if ai.tag != 'invalid']
                    ids = [li.identifier for li in lns]

                    self._make_level(doc, irrad, level, ids, ans)
            else:
                if grouped_identifiers:
                    for lns in grouped_identifiers:
                        lis = [db.get_labnumber(li) for li in lns]
                        self._make_multi_panel_labnumbers(doc, lis)

                else:
                    if identifiers:
                        lns = [db.get_labnumber(li) for li in identifiers]
                    else:
                        lns = [ln for proj in projects
                               for si in db.get_samples(project=proj)
                               for ln in si.labnumbers]
                    self._make_labnumbers(doc, lns)

    def _make_level(self, doc, irrad, level, ids, ans):
        root = doc['root']
        options = doc['options']

        lroot = os.path.join(root, irrad, level)
        r_mkdir(lroot)

        n = len(ans)
        prog = self.open_progress(n, close_at_end=False)

        ans = self.make_analyses(ans, progress=prog, use_cache=False)
        #group by stepheat vs fusion
        pred = lambda x: bool(x.step)

        ans = sorted(ans, key=pred)
        stepheat, fusion = map(list, partition(ans, pred))

        # apred = lambda x: x.aliquot
        # stepheat = sorted(stepheat, key=apred)
        # if stepheat:
        #     self._make_editor(stepheat, 'step_heat', options, prog, ln_root, li)
        project = 'J'
        # lns=[li.identifier for li in level.labnumbers]

        if fusion:
            save_args = (lroot, level, '{} {}'.format(irrad, level),
                         project, ids)
            self._make_editor(fusion, ('fusion', 'fusion_grouped'),
                              options, prog, 'aliquot', False,
                              save_args)
        prog.close()

    def _make_multi_panel_labnumbers(self, doc, lns):
        root = doc['root']
        options = doc['options']

        ans = [ai for li in lns for ai in li.analyses]
        ans = filter(lambda x: not x.tag == 'invalid', ans)
        # prog = self.open_progress(len(ans), close_at_end=False)
        # ans = self.make_analyses(ans,
        #                          progress=prog,
        #                          use_cache=False)
        # print lns
        prog = None
        pred = lambda x: bool(x.step)

        ident = ','.join([li.identifier for li in lns])
        li = ident

        ln_root = os.path.join(root, ident)
        r_mkdir(ln_root)

        ans = sorted(ans, key=pred)
        stepheat, fusion = map(list, partition(ans, pred))
        project = 'Minna Bluff'
        if stepheat and options.has_key('step_heat'):
            key = lambda x: x.aliquot
            stepheat = sorted(stepheat, key=key)
            for aliquot, ais in groupby(stepheat, key=key):
                name = make_runid(li, aliquot, '')
                self._make_editor(ais, 'step_heat', options, prog, False,
                                  True,
                                  (ln_root, name, name, project, (li,)))

        if fusion and options.has_key('fusion'):
            self._make_editor(fusion, 'fusion', options, prog, False,
                              True,
                              (ln_root, 'fig', li, project, (li,)))

    def _make_labnumbers(self, doc, lns):
        root = doc['root']
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

        #filter invalid analyses
        ans = filter(lambda x: not x.tag == 'invalid', li.analyses)

        #group by stepheat vs fusion
        pred = lambda x: bool(x.step)

        ans = sorted(ans, key=pred)
        stepheat, fusion = map(list, partition(ans, pred))

        project = 'Minna Bluff'

        li = li.identifier
        if stepheat:
            key = lambda x: x.aliquot
            stepheat = sorted(stepheat, key=key)

            if options.has_key('step_heat'):
                for aliquot, ais in groupby(stepheat, key=key):
                    name = make_runid(li, aliquot, '')
                    self._make_editor(ais, 'step_heat', options, prog, False,
                                      False,
                                      (ln_root, name, name, project, (li,)))
            if options.has_key('isochron'):
                for aliquot, ais in groupby(stepheat, key=key):
                    name = make_runid(li, aliquot, '')
                    self._make_editor(ais, 'isochron', options, prog, False,
                                      False,
                                      (ln_root, '{}_isochron'.format(name), name, project, (li,)))

        if fusion and options.has_key('fusion'):
            self._make_editor(fusion, 'fusion', options, prog, False,
                              False,
                              (ln_root, li, li, project, (li,)))

    def _make_editor(self, ans, editor_name, options, prog, apply_grouping,
                     apply_graph_grouping,
                     save_args):
        if isinstance(editor_name, tuple):
            editor_name, save_name = editor_name
        else:
            editor_name, save_name = editor_name, editor_name

        editor = getattr(self, '_{}_editor'.format(editor_name))
        if editor is None:
            klass = getattr(self, '{}_editor_klass'.format(editor_name))
            editor = klass(processor=self)
            editor.plotter_options_manager.set_plotter_options(options[editor_name])

        # unks = self.make_analyses(ans, progress=prog, use_cache=False)
        editor.set_items(ans, progress=prog, update_graph=False, use_cache=False)
        if apply_grouping:
            group_analyses_by_key(editor, editor.analyses, apply_grouping)

        if apply_graph_grouping:
            ts = []
            unks = editor.analyses
            for i, (si, gi) in enumerate(groupby(unks, key=lambda x: x.sample)):
                idxs = [unks.index(ai) for ai in gi]
                editor.set_graph_group(idxs, i)
                ts.append(si)
            editor.titles = ts

        editor.clear_aux_plot_limits()
        editor.rebuild()

        func = getattr(self, '_save_{}'.format(save_name))
        func(editor, *save_args)
        setattr(self, '_{}_editor'.format(editor_name), editor)
        del editor

    #save
    def _save_isochron(self, editor, *args):
        self._save(editor, *args)
        if self._save_interpreted:
            editor.save_interpreted_ages()

    def _save_step_heat(self, editor, *args):
        self._save(editor, *args)
        if self._save_interpreted:
            editor.save_interpreted_ages()

    def _save_fusion_grouped(self, *args):
        self._save(*args)

    def _save_fusion(self, editor, *args):
        self._save_labnumber(editor, *args)
        if self._save_interpreted:
            editor.save_interpreted_ages()

    def _save_labnumber(self, editor, root, pathname, name, project, lns):
        self._save(editor, root, pathname, name, project, lns)

    def _save(self, editor, root, pathname, name, project, lns):
        if self._save_pdf_figure:
            p, _ = unique_path(root, pathname, extension='.pdf')
            editor.save_file(p, dest_box=(1.5, 1, 6, 9))

        if self._save_db_figure:
            editor.save_figure('EasyFigure {}'.format(name),
                               project, lns)


#============= EOF =============================================
