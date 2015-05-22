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
from traits.api import HasTraits, Str, Instance, List, Event, Bool, on_trait_change
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
from pychron.pipeline.nodes.figure import IdeogramNode, SpectrumNode, FigureNode, SeriesNode
from pychron.pipeline.nodes.filter import FilterNode
from pychron.pipeline.nodes.fit import FitIsotopeEvolutionNode, FitBlanksNode, FitICFactorNode
from pychron.pipeline.nodes.grouping import GroupingNode
from pychron.pipeline.nodes.persist import PDFFigureNode, IsotopeEvolutionPersistNode, \
    BlanksPersistNode, ICFactorPersistNode
from pychron.pipeline.template import PipelineTemplate


class Pipeline(HasTraits):
    name = Str('Pipeline')
    nodes = List

    @on_trait_change('nodes[]')
    def _handle_nodes_changed(self):
        for i, ni in enumerate(self.nodes):
            for na, nb in ((FitICFactorNode, ICFactorPersistNode),
                           (FitBlanksNode, BlanksPersistNode)):
                if isinstance(ni, na):
                    for nj in self.nodes[i + 1:]:
                        if isinstance(nj, nb):
                            ni.has_save_node = True

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
    selected = Instance(BaseNode)

    unknowns = List
    references = List
    run_needed = Event
    refresh_all_needed = Event
    update_needed = Event
    refresh_table_needed = Event

    show_group_colors = Bool

    selected_pipeline_template = Str
    available_pipeline_templates = List

    selected_unknowns = List
    selected_references = List
    dclicked_unknowns = Event
    dclicked_references = Event

    recall_analyses_needed = Event

    def __init__(self, *args, **kw):
        super(PipelineEngine, self).__init__(*args, **kw)

        self._load_predefined_templates()

    def reset(self):
        for ni in self.pipeline.nodes:
            ni.visited = False

        self.update_needed = True

    def update_detectors(self):
        for p in self.pipeline.nodes:
            if isinstance(p, FitICFactorNode):
                udets = {iso.detector for ai in self.unknowns
                         for iso in ai.isotopes.itervalues()}
                rdets = {iso.detector for ai in self.references
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
        self.update_needed = True

        # if node.configure():
        # node.refresh()
        # self.run_needed = node

    def refresh_analyses(self):
        unks = []
        refs = []
        for node in self.pipeline.nodes:
            if isinstance(node, ReferenceNode):
                refs.extend(node.analyses)
            elif isinstance(node, UnknownNode):
                unks.extend(node.analyses)

        self.unknowns = unks
        self.references = refs

    def remove_node(self, node):
        self.pipeline.nodes.remove(node)
        self.run_needed = True

    def set_template(self, name):
        self._set_template(name)

    # def add_analyses(self, node):
    # """
    # add analyses to node
    #
    # select analyses from popup browser
    #     :param node:
    #     :return:
    #     """
    #     browser_view = BrowserView(model=self.browser_model)
    #     info = browser_view.edit_traits(kind='livemodal')
    #     if info.result:
    #         records = self.browser_model.get_analysis_records()
    #         if records:
    #             analyses = self.dvc.make_analyses(records)
    #             node.analyses.extend(analyses)
    #
    #             self.refresh_analyses()

    # debugging
    def select_default(self):
        node = self.pipeline.nodes[0]

        self.browser_model.select_sample(idx=0)
        records = self.browser_model.get_analysis_records()
        analyses = self.dvc.make_analyses(records)
        node.analyses.extend(analyses)
        self.refresh_analyses()

    def add_test_filter(self):
        node = self.pipeline.nodes[-1]
        newnode = FilterNode()
        filt = newnode.filters[0]
        filt.attribute = 'uage'
        filt.comparator = '<'
        filt.criterion = '10'

        self.pipeline.add_after(node, newnode)

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

        self.refresh_analyses()

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

    def run(self, state, run_to):
        start_node = state.veto
        self.debug('pipeline run started')
        if start_node:
            self.debug('starting at node {}'.format(start_node))
        state.veto = None

        for idx, node in enumerate(self.pipeline.iternodes(start_node, run_to)):
            self.selected = node
            node.visited = True
            self.update_needed = True
            if node.enabled:
                self.debug('Run node {:02n}: {}'.format(idx, node))
                node.run(state)

                if state.veto:
                    self.debug('pipeline vetoed by {}'.format(node))
                    self.refresh_analyses()
                    return
            else:
                self.debug('Skip node {:02n}: {}'.format(idx, node))
        else:
            self.debug('pipeline run finished')
            self.refresh_analyses()
            # self.selected = None
            # self.update_needed = True
            return True

            # self.unknowns = state.unknowns
            # self.references = state.references

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
                    self.unknowns = editor.analyses
                    self.selected = node
                    break

    # private
    def _set_template(self, name):
        path = os.path.join(paths.pipeline_template_dir, add_extension(name, '.yaml'))
        if not os.path.isfile(path):
            self.warning('Invalid template name. {} does not exist'.format(path))
            return

        pt = PipelineTemplate(name, path)
        pt.render(self.pipeline, self.browser_model, self.dvc)
        self.update_detectors()
        # self.update_unknowns()
        # self.update_references()

    def _load_predefined_templates(self):
        templates = []
        for temp in list_directory2(paths.pipeline_template_dir, extension='.yaml',
                                    remove_extension=True):
            templates.append(temp)

        self.available_pipeline_templates = templates

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

    def _dclicked_unknowns_fired(self):
        self.recall_unknowns()

    def _dclicked_references_fired(self):
        self.recall_references()

    def _selected_pipeline_template_changed(self, new):
        if new:
            self.debug('Pipeline template {} selected'.format(new))
            self._set_template(new)
            # pt = PipelineTemplate(new)

    def _selected_changed(self, new):
        self.show_group_colors = False
        if isinstance(new, UnknownNode):
            self.unknowns = new.analyses
        elif isinstance(new, ReferenceNode):
            self.references = new.analyses
        elif isinstance(new, FigureNode):
            self.show_group_colors = True
            if new.editor:
                self.unknowns = new.editor.analyses
                self.task.activate_editor(new.editor)

                # self.update_needed = True

# if __name__ == '__main__':
# from traitsui.api import TreeNode, Handler
# from pychron.core.ui.tree_editor import TreeEditor
# from pyface.action.menu_manager import MenuManager
# from pychron.pipeline.nodes.base import BaseNode
# from traitsui.menu import Action
# from pychron.envisage.resources import icon
# from pychron.core.helpers.logger_setup import logging_setup
#
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


# ============= EOF =============================================
