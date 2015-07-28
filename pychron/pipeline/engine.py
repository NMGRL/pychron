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
import time

from traits.api import HasTraits, Str, Instance, List, Event, on_trait_change

# ============= standard library imports ========================
import os
import yaml
# ============= local library imports  ==========================
from pychron.core.helpers.filetools import list_directory2, add_extension
from pychron.paths import paths
from pychron.pipeline.nodes import FindReferencesNode
from pychron.pipeline.nodes.base import BaseNode
from pychron.pipeline.nodes.data import UnknownNode, ReferenceNode
from pychron.loggable import Loggable
from pychron.pipeline.nodes.figure import IdeogramNode, SpectrumNode, FigureNode, SeriesNode, NoAnalysesError
from pychron.pipeline.nodes.filter import FilterNode
from pychron.pipeline.nodes.fit import FitIsotopeEvolutionNode, FitBlanksNode, FitICFactorNode, FitFluxNode, FitNode
from pychron.pipeline.nodes.grouping import GroupingNode
from pychron.pipeline.nodes.persist import PDFFigureNode, IsotopeEvolutionPersistNode, \
    BlanksPersistNode, ICFactorPersistNode, FluxPersistNode, PersistNode
from pychron.pipeline.template import PipelineTemplate

TEMPLATE_NAMES = ('Iso Evo', 'Icfactor', 'Blanks', 'Flux', 'Ideogram', 'Spectrum',
                  'Isochron', 'Series', 'Table')


class Pipeline(HasTraits):
    name = Str('Pipeline')
    nodes = List

    def reset(self, clear_data=False):
        for ni in self.nodes:
            if isinstance(ni, UnknownNode) and clear_data:
                ni.clear_data()

            ni.reset()

    @on_trait_change('nodes[]')
    def _handle_nodes_changed(self):
        for i, ni in enumerate(self.nodes):
            for na, nb in ((FitICFactorNode, ICFactorPersistNode),
                           (FitBlanksNode, BlanksPersistNode),
                           (FitIsotopeEvolutionNode, IsotopeEvolutionPersistNode),
                           (FitFluxNode, FluxPersistNode)):
                if isinstance(ni, na):
                    for nj in self.nodes[i + 1:]:
                        if isinstance(nj, nb):
                            ni.has_save_node = True

    def get_experiment_ids(self):
        ps = set()
        for node in self.nodes:
            if isinstance(node, UnknownNode):
                ps = ps.union({ai.experiment_identifier for ai in node.unknowns})
        return ps

    def move_up(self, node):
        idx = self.nodes.index(node)
        if idx > 1:
            self.nodes.remove(node)
            self.nodes.insert(idx - 1, node)

    def move_down(self, node):
        idx = self.nodes.index(node)
        if idx < len(self.nodes) - 1:
            self.nodes.remove(node)
            self.nodes.insert(idx + 1, node)

    def add_after(self, after, node):
        if after:
            idx = self.nodes.index(after)
            self.nodes.insert(idx + 1, node)
        else:
            self.nodes.append(node)

    def to_template(self):
        nodes = [ni.to_template() for ni in self.nodes]
        return nodes

    def iternodes(self, start_node=None, run_to=None):
        if run_to:
            return self.nodes[:self.nodes.index(run_to) + 1]
        else:
            if start_node is None:
                idx = -1
            else:
                idx = self.nodes.index(start_node)

            try:
                return self.nodes[idx + 1:]
            except IndexError:
                return []


class PipelineEngine(Loggable):
    dvc = Instance('pychron.dvc.dvc.DVC')
    browser_model = Instance('pychron.envisage.browser.base_browser_model.BaseBrowserModel')
    pipeline = Instance(Pipeline, ())
    selected = Instance(BaseNode, ())
    dclicked = Event
    active_editor = Event

    # unknowns = List
    # references = List
    run_needed = Event
    refresh_all_needed = Event
    update_needed = Event
    refresh_table_needed = Event

    # show_group_colors = Bool

    selected_pipeline_template = Str
    available_pipeline_templates = List

    selected_unknowns = List
    selected_references = List
    dclicked_unknowns = Event
    dclicked_references = Event

    recall_analyses_needed = Event
    reset_event = Event

    tag_event = Event
    invalid_event = Event
    recall_event = Event

    def __init__(self, *args, **kw):
        super(PipelineEngine, self).__init__(*args, **kw)

        self._load_predefined_templates()

    def drop_factory(self, items):

        return self.dvc.make_analyses(items)

    def reset(self):
        # for ni in self.pipeline.nodes:
        #     ni.visited = False
        self.pipeline.reset()
        self.update_needed = True

    def update_detectors(self):
        """
        set valid detectors for FitICFactorNodes

        """
        for p in self.pipeline.nodes:
            if isinstance(p, FitICFactorNode):
                udets = {iso.detector for ai in p.unknowns
                         for iso in ai.isotopes.itervalues()}
                rdets = {iso.detector for ai in p.references
                         for iso in ai.isotopes.itervalues()}

                p.set_detectors(list(udets.union(rdets)))

    def recall_unknowns(self):
        self.debug('recall unks')
        self.recall_analyses_needed = self.selected_unknowns

    def recall_references(self):
        self.debug('recall refs')
        self.recall_analyses_needed = self.selected_references

    def review_node(self, node):
        node.reset()
        self.run_needed = True
        # if node.review():
        #     self.run_needed = True

    def configure(self, node):
        node.configure()
        osel = self.selected
        self.update_needed = True
        self.selected = osel

    def remove_node(self, node):
        self.pipeline.nodes.remove(node)
        self.run_needed = True

    def set_template(self, name):
        self.reset_event = True
        self._set_template(name)

    def get_experiment_ids(self):
        return self.pipeline.get_experiment_ids()

    # debugging
    def select_default(self):
        node = self.pipeline.nodes[0]

        self.browser_model.select_project('J-Curve')
        self.browser_model.select_experiment('Irradiation-NM-272')
        self.browser_model.select_sample(idx=0)
        records = self.browser_model.get_analysis_records()
        if records:
            analyses = self.dvc.make_analyses(records)
            # print len(records),len(analyses)
            node.unknowns.extend(analyses)
            node._manual_configured = True
            # self.refresh_analyses()

    def add_test_filter(self):
        node = self.pipeline.nodes[-1]
        newnode = FilterNode()
        filt = newnode.filters[0]
        filt.attribute = 'uage'
        filt.comparator = '<'
        filt.criterion = '10'

        self.pipeline.add_after(node, newnode)

    def clear(self):
        self.unknowns = []
        self.references = []
        for ni in self.pipeline.nodes:
            ni.clear_data()

            # self.pipeline.nodes = []
            # self.selected_pipeline_template = ''
            # self._set_template(self.selected_pipeline_template)

    # ============================================================================================================
    # nodes
    # ============================================================================================================
    # data

    def add_data(self, node=None, run=False):
        """

        add a default data node
        :return:
        """

        self.debug('add data node')
        newnode = UnknownNode(dvc=self.dvc, browser_model=self.browser_model)
        node = self._get_last_node(node)
        self.pipeline.add_after(node, newnode)

    def add_references(self, node=None, run=False):
        newnode = ReferenceNode(name='references', dvc=self.dvc, browser_model=self.browser_model)
        node = self._get_last_node(node)
        self.pipeline.add_after(node, newnode)

    # preprocess
    def add_filter(self, node=None, run=True):
        newnode = FilterNode()
        self._add_node(node, newnode, run)

    def add_grouping(self, node=None, run=True):
        newnode = GroupingNode()
        self._add_node(node, newnode, run)

    # find
    def add_find_airs(self, node=None, run=True):
        self._add_find_node(node, run, 'air')

    def add_find_blanks(self, node=None, run=True):
        self._add_find_node(node, run, 'blank_unknown')

    # figures
    def add_spectrum(self, node=None, run=True):
        newnode = SpectrumNode()
        self._add_node(node, newnode, run)

    def add_ideogram(self, node=None, run=True):
        ideo_node = IdeogramNode()
        self._add_node(node, ideo_node, run)

    def add_series(self, node=None, run=True):
        series_node = SeriesNode()
        self._add_node(node, series_node, run)

    # fits
    def add_icfactor(self, node=None, run=True):
        new = FitICFactorNode()
        if new.configure():
            node = self._get_last_node(node)
            self.pipeline.add_after(node, new)
            if new.use_save_node:
                self.add_icfactor_persist(new, run=False)
            if run:
                self.run_needed = True

    def add_blanks(self, node=None, run=True):
        new = FitBlanksNode()
        if new.configure():
            node = self._get_last_node(node)
            self.pipeline.add_after(node, new)
            if new.use_save_node:
                self.add_blanks_persist(new, run=False)
            if run:
                self.run_needed = True

    def add_isotope_evolution(self, node=None, run=True):
        new = FitIsotopeEvolutionNode()
        if new.configure():
            node = self._get_last_node(node)

            self.pipeline.add_after(node, new)
            if new.use_save_node:
                self.add_iso_evo_persist(new, run=False)

            if run:
                self.run_needed = new

    # save
    def add_icfactor_persist(self, node=None, run=True):
        new = ICFactorPersistNode(dvc=self.dvc)
        self._add_node(node, new, run)

    def add_blanks_persist(self, node=None, run=True):
        new = BlanksPersistNode(dvc=self.dvc)
        self._add_node(node, new, run)

    def add_iso_evo_persist(self, node=None, run=True):
        new = IsotopeEvolutionPersistNode(dvc=self.dvc)
        self._add_node(node, new, run)

    def add_pdf_figure(self, node=None, run=True):
        newnode = PDFFigureNode(root='/Users/ross/Sandbox')
        self._add_node(node, newnode, run=run)

    # ============================================================================================================
    def save_pipeline_template(self, path):
        self.info('Saving pipeline to {}'.format(path))
        with open(path, 'w') as wfile:
            obj = self.pipeline.to_template()
            yaml.dump(obj, wfile, default_flow_style=False)

    def run_persist(self, state):
        for node in self.pipeline.iternodes():
            if not isinstance(node, (FitNode, PersistNode)):
                continue

            node.run(state)
            if state.canceled:
                self.debug('pipeline canceled by {}'.format(node))
                return True

    def run(self, state, run_to):
        ost = time.time()
        start_node = state.veto
        self.debug('pipeline run started')
        if start_node:
            self.debug('starting at node {}'.format(start_node))
        state.veto = None

        for node in self.pipeline.iternodes(start_node, run_to):
            node.visited = False

        for idx, node in enumerate(self.pipeline.iternodes(start_node, run_to)):

            if node.enabled:
                node.editor = None

                node.active = True
                if not node.pre_run(state):
                    return True
                node.active = False

                st = time.time()
                try:
                    node.run(state)
                    node.visited = True
                    self.selected = node
                except NoAnalysesError:
                    self.information_dialog('No Analyses in Pipeline!')
                    self.pipeline.reset()
                    return True
                self.debug('{:02n}: {} Runtime: {:0.4f}'.format(idx, node, time.time() - st))

                if state.veto:
                    self.debug('pipeline vetoed by {}'.format(node))
                    return

                if state.canceled:
                    self.debug('pipeline canceled by {}'.format(node))
                    return True

            else:
                self.debug('Skip node {:02n}: {}'.format(idx, node))
        else:
            self.debug('pipeline run finished')
            self.debug('pipeline runtime {}'.format(time.time() - ost))

            return True

    def post_run(self, state):
        self.debug('pipeline post run started')
        for idx, node in enumerate(self.pipeline.nodes):
            action = 'skip'
            if node.enabled:
                action = 'post run'
                node.post_run(state)
            self.debug('{} node {:02n}: {}'.format(action, idx, node.name))
        self.debug('pipeline post run finished')

        self.update_needed = True
        self.refresh_table_needed = True

    def select_node_by_editor(self, editor):
        for node in self.pipeline.nodes:
            if hasattr(node, 'editor'):
                if node.editor == editor:
                    self.selected = node
                    # self.unknowns = editor.analyses
                    self.refresh_table_needed = True
                    break

    # private
    def _set_template(self, name):
        print 'set template', name
        name = name.replace(' ', '_').lower()

        path = os.path.join(paths.pipeline_template_dir, add_extension(name, '.yaml'))
        if not os.path.isfile(path):
            self.warning('Invalid template name. {} does not exist'.format(path))
            return

        pt = PipelineTemplate(name, path)
        pt.render(self.pipeline, self.browser_model, self.dvc)
        self.update_detectors()
        if self.pipeline.nodes:
            self.selected = self.pipeline.nodes[0]

    def _load_predefined_templates(self):
        templates = []
        for temp in list_directory2(paths.pipeline_template_dir, extension='.yaml',
                                    remove_extension=True):
            templates.append(temp)

        def formatter(t):
            return ' '.join(map(str.capitalize, t.split('_')))

        templates = map(formatter, templates)

        ns = [pt for pt in TEMPLATE_NAMES if pt in templates]
        self.available_pipeline_templates = ns

    def _add_find_node(self, node, run, analysis_type):
        newnode = FindReferencesNode(dvc=self.dvc, analysis_type=analysis_type)
        if newnode.configure():
            node = self._get_last_node(node)

            self.pipeline.add_after(node, newnode)
            self.add_references(newnode, run=False)

            if run:
                self.run_needed = newnode

    def _add_node(self, node, new, run=True):
        if new.configure():
            node = self._get_last_node(node)

            self.pipeline.add_after(node, new)
            if run:
                self.run_needed = new

    def _get_last_node(self, node=None):
        if node is None:
            if self.pipeline.nodes:
                idx = len(self.pipeline.nodes) - 1

                node = self.pipeline.nodes[idx]
        return node

    # handlers
    def _dclicked_unknowns_changed(self):
        if self.selected_unknowns:
            self.recall_unknowns()

    def _dclicked_references_fired(self):
        if self.selected_references:
            self.recall_references()

    def _selected_pipeline_template_changed(self, new):
        if new:
            self.debug('Pipeline template {} selected'.format(new))
            self._set_template(new)

    def _selected_changed(self, old, new):
        if old:
            old.on_trait_change(self._handle_tag, 'unknowns:tag_event,references:tag_event', remove=True)
            old.on_trait_change(self._handle_invalid, 'unknowns:invalid_event,references:invalid_event', remove=True)
            old.on_trait_change(self._handle_recall, 'unknowns:recall_event,references:recall_event', remove=True)
            old.on_trait_change(self._handle_len_unknowns, 'unknowns_items', remove=True)
            old.on_trait_change(self._handle_len_references, 'references_items', remove=True)

        if new:
            new.on_trait_change(self._handle_tag, 'unknowns:tag_event,references:tag_event')
            new.on_trait_change(self._handle_invalid, 'unknowns:invalid_event,references:invalid_event')
            old.on_trait_change(self._handle_recall, 'unknowns:recall_event,references:recall_event')
            new.on_trait_change(self._handle_len_unknowns, 'unknowns_items')
            new.on_trait_change(self._handle_len_references, 'references_items')
            # new.on_trait_change(self._handle_unknowns, 'unknowns[]')

        # self.show_group_colors = False
        if isinstance(new, FigureNode):
            # self.show_group_colors = True
            if new.editor:
                self.active_editor = new.editor

    # _suppress_handle_unknowns = False
    # def _handle_unknowns(self, obj, name, new):
    #     if self._suppress_handle_unknowns:
    #         return
    #
    #     items = obj.unknowns
    #
    #     for i, item in enumerate(items):
    #         if not isinstance(item, DVCAnalysis):
    #             self._suppress_handle_unknowns = True
    #             nitem = self.dvc.make_analyses((item,))[0]
    #             obj.unknowns.pop(i)
    #             obj.unknowns.insert(i, nitem)
    #
    #     self._suppress_handle_unknowns = False
    #     print 'asdfasdfasfsafs', obj, new

    _len_unknowns_cnt = 0
    _len_unknowns_removed = 0
    _len_references_cnt = 0
    _len_references_removed = 0

    def _handle_len_unknowns(self, new):
        self._handle_len('unknowns', lambda e: e.set_items(self.selected.unknowns))

    def _handle_len_references(self, new):
        self._handle_len('references', lambda e: e.set_references(self.selected.references))

    def _handle_len(self, k, func):
        lr = '_len_{}_removed'.format(k)
        lc = '_len_{}_cnt'.format(k)

        editor = None
        if hasattr(self.selected, 'editor'):
            editor = self.selected.editor

        if editor:
            n = len(getattr(self, 'selected_{}'.format(k)))
            if not n:
                setattr(self, lc, getattr(self, lc) + 1)

            else:
                setattr(self, lc, 0)
                setattr(self, lr, n)

            if getattr(self, lc) >= getattr(self, lr) or n == 1:
                setattr(self, lc, 0)
                # self._len_references_cnt = 0
                func(editor)
                # editor.set_references(self.selected.references)
                editor.refresh_needed = True

    def _handle_recall(self, new):
        self.recall_event = new

    def _handle_tag(self, new):
        self.tag_event = new

    def _handle_invalid(self, new):
        self.invalid_event = new

    def _dclicked_changed(self, new):
        self.configure(new)
        # self.update_needed = True

# ============= EOF =============================================

# if __name__ == '__main__':
# from traitsui.api import TreeNode, Handler
# from pychron.core.ui.tree_editor import TreeEditor
# from pyface.action.menu_manager import MenuManager
# from pychron.pipeline.nodes.base import BaseNode
# from traitsui.menu import Action
# from pychron.envisage.resources import icon
# from pychron.core.helpers.logger_setup import logging_setup
# @on_trait_change('unknowns[]')
# def _handle_unknowns(self, name, old, new):
#     if not new:
#         # only update if deletion
#         for n in self.pipeline.nodes:
#             try:
#                 n.editor.set_items(self.unknowns)
#                 n.refresh()
#             except AttributeError:
#                 pass
#
# @on_trait_change('references[]')
# def _handle_unknowns(self, name, old, new):
#     if not new:
#         # only update if deletion
#         for n in self.pipeline.nodes:
#             try:
#                 n.editor.set_references(self.references)
#                 n.refresh()
#             except AttributeError:
#                 pass
# self.show_group_colors = False
#     if isinstance(new, (UnknownNode, FluxMonitorsNode)):
#         self.unknowns = new.analyses
#     elif isinstance(new, ReferenceNode):
#         self.references = new.analyses
#     elif isinstance(new, FigureNode):
#         self.show_group_colors = True
#         if new.editor:
#             self.unknowns = new.editor.analyses
#             self.active_editor = new.editor
# logging_setup('pipeline')
# class PipelineHandler(Handler):
#         def add_data(self, info, obj):
#             info.object.add_data()
#
#     class DataTreeNode(TreeNode):
#         def get_icon( self, object, is_expanded ):
#             return icon('table')
#
#     e = PipelineEngine()
#     # e.add_data()
#     # e.add_node('foo')
#     # e.add_node('bar')
#     nodes = [TreeNode(node_for=[Pipeline],
#                       children='nodes',
#                       icon_open='',
#                       label='name',
#                       auto_open=True,
#                       menu=MenuManager(Action(name='Add Data',
#                                                    action='add_data'))),
#              # TreeNode(node_for=[BaseNode],
#              #
#              #          label='name'),
#              DataTreeNode(node_for=[DataNode],
#                           label='name')
#              ]
#     editor = TreeEditor(nodes=nodes,
#                         editable=False,
#                         selection_mode='extended',
#                         selected='selected',
#                         dclick='dclicked',
#                         show_disabled=True,
#                         refresh_all_icons='refresh_all_needed',
#                         refresh_icons='refresh_needed'
#                         )
#     v = View(UItem('pipeline',
#                    editor=editor),
#              handler=PipelineHandler())
#     e.configure_traits(view=v)

# def refresh_analyses(self):
#     unks = []
#     refs = []
#     for node in self.pipeline.nodes:
#         if isinstance(node, ReferenceNode):
#             refs.extend(node.analyses)
#         elif isinstance(node, (UnknownNode, FluxMonitorsNode)):
#             unks.extend(node.analyses)
#
#     self.unknowns = unks
#     self.references = refs
