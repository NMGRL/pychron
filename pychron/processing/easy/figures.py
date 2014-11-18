# ===============================================================================
# Copyright 2013 Jake Ross
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

        opt = ep.doc('figures')
        self._config_options = opt
        self._save_db_figure = opt['save_db_figure']
        self._save_pdf_figure = opt['save_pdf_figure']
        self._save_interpreted = opt['save_interpreted']

        projects = opt['projects']
        identifiers = opt.get('identifiers')
        grouped_identifiers = opt.get('identifier_groups', None)

        # grouped_identifiers = doc.get('identifier_groups', None)
        levels = opt.get('levels')

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

                    self._make_level(opt, irrad, level, ids, ans)
            else:
                if grouped_identifiers:
                    groupby_aliquot = opt.get('groupby_aliquot', False)
                    figures_per_page = opt.get('figures_per_page', 4)
                    excludes = opt.get('excludes', None)
                    cnt = 1
                    gen = self._analysis_block_gen(grouped_identifiers,
                                                   groupby_aliquot,
                                                   excludes)
                    while 1:

                        ans = []

                        for _ in range(figures_per_page):
                            try:
                                ans.extend(gen.next())
                            except StopIteration:
                                break

                        if ans:
                            self._make_multi_panel_labnumbers(ans, cnt)
                            cnt += 1
                        else:
                            break

                            # for i,lns in enumerate(grouped_identifiers):
                            #     lis = [db.get_labnumber(li) for li in lns]
                            #     self._make_multi_panel_labnumbers(doc, lis, i+1)

                else:
                    if identifiers:
                        lns = [db.get_labnumber(li) for li in identifiers]
                    else:
                        lns = [ln for proj in projects
                               for si in db.get_samples(project=proj)
                               for ln in si.labnumbers]
                    self._make_labnumbers(opt, lns)

    def _analysis_block_gen(self, lns, groupby_aliquot, excludes):
        db = self.db
        if excludes is None:
            excludes = []

        def gen():
            for li in lns:
                ans = []
                dbli = db.get_labnumber(li)
                ans.extend([ai for ai in dbli.analyses if ai.tag != 'invalid'])
                if groupby_aliquot:
                    key = lambda x: x.aliquot
                    for ali, ais in groupby(ans, key=key):
                        if '{}-{:02n}'.format(li, ali) in excludes:
                            continue
                        yield ais
                else:
                    yield ans

        return gen()

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

    def _make_multi_panel_labnumbers(self, ans, cnt):

        root = self._config_options['root']
        options = self._config_options['options']
        # ans = [ai for li in lns for ai in li.analyses]
        # ans = filter(lambda x: not x.tag == 'invalid', ans)
        # prog = self.open_progress(len(ans), close_at_end=False)
        # ans = self.make_analyses(ans,
        #                          progress=prog,
        #                          use_cache=False)
        # print lns
        lns = list({ai.labnumber.identifier for ai in ans})
        print len(lns)
        prog = None
        pred = lambda x: bool(x.step)

        ident = ','.join([li for li in lns])
        li = ident

        ident = '{:03n}-{}'.format(cnt, ident)
        ln_root = os.path.join(root, ident)
        r_mkdir(ln_root)
        ans = sorted(ans, key=pred)
        stepheat, fusion = map(list, partition(ans, pred))
        project = 'Minna Bluff'
        if stepheat and options.has_key('step_heat'):
            # key = lambda x: x.aliquot
            # stepheat = sorted(stepheat, key=key)
            # for aliquot, ais in groupby(stepheat, key=key):
            # name = make_runid(li, aliquot, '')
            self._make_editor(ans, 'step_heat', options, prog, False,
                              lambda x: '{}-{}'.format(x.identifier, x.aliquot),
                              (ln_root, 'spec', li, project, (li,)))

        if fusion and options.has_key('fusion'):
            self._make_editor(fusion, 'fusion', options, prog, False,
                              lambda x: x.identifier,
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

        editor.set_items(ans, progress=prog, update_graph=False, use_cache=False)
        if apply_grouping:
            group_analyses_by_key(editor, editor.analyses, apply_grouping)

        if apply_graph_grouping:
            unks = editor.analyses

            unks = sorted(unks, key=apply_graph_grouping)
            editor.analyses = unks
            for i, (si, gi) in enumerate(groupby(unks, key=apply_graph_grouping)):
                for ai in gi:
                    ai.graph_id = i
                    # idxs = [unks.index(ai) for ai in gi]
                    # editor.set_graph_group(idxs, i)

            # fill add placeholder graphs
            #if n <= than 3 (should be ncols) repeat unks
            ncol = 2
            if i < ncol:
                for j in range(ncol - i):
                    uc = unks[0].clone_traits()
                    uc.graph_id = i + j + 1
                    unks.extend([uc])
                editor.analyses = unks

        editor.show_caption = self._config_options.get('show_caption', False)
        editor.caption_path = self._config_options.get('caption_path', None)
        editor.caption_text = self._config_options.get('caption_text', None)

        editor.clear_aux_plot_limits()
        editor.rebuild()

        func = getattr(self, '_save_{}'.format(save_name))
        func(editor, *save_args)
        setattr(self, '_{}_editor'.format(editor_name), editor)

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
