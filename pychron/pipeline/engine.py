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

from traits.api import HasTraits, Str, Instance, List, Event, Bool

# ============= standard library imports ========================
# ============= local library imports  ==========================
import yaml
from pychron.core.helpers.filetools import list_directory2, add_extension
from pychron.paths import paths
from pychron.pipeline.nodes.base import BaseNode
from pychron.pipeline.nodes.data import UnknownNode, ReferenceNode
from pychron.loggable import Loggable
from pychron.pipeline.nodes.figure import IdeogramNode, SpectrumNode, FigureNode, SeriesNode
from pychron.pipeline.nodes.filter import FilterNode
from pychron.pipeline.nodes.fit import IsotopeEvolutionNode
from pychron.pipeline.nodes.grouping import GroupingNode
from pychron.pipeline.nodes.persist import PDFFigureNode, IsotopeEvolutionPersistNode
from pychron.pipeline.template import PipelineTemplate


class Pipeline(HasTraits):
    name = Str('Pipeline')
    nodes = List

    def add_after(self, after, node):
        idx = self.nodes.index(after)
        self.nodes.insert(idx + 1, node)

    def to_template(self):
        nodes = [ni.to_template() for ni in self.nodes]
        return nodes


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

    def __init__(self, *args, **kw):
        super(PipelineEngine, self).__init__(*args, **kw)

        self._load_predefined_templates()

    def configure(self, node):

        if node.configure():
            self.run_needed = True

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

    def add_data(self, node=None, run=False):
        """

        add a default data node
        :return:
        """
        self.debug('add data node')
        # self._add_node()
        self.pipeline.nodes.append(UnknownNode(name='default',
                                               dvc=self.dvc,
                                               browser_model=self.browser_model))
        self.refresh_analyses()

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
    # preprocess
    def add_filter(self, node=None, run=True):
        newnode = FilterNode()
        self._add_node(node, newnode, run)

    def add_grouping(self, node=None, run=True):
        newnode = GroupingNode()
        self._add_node(node, newnode, run)

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
    def add_isotope_evolution(self, node=None, run=True):
        new = IsotopeEvolutionNode()
        # self._add_node(node, newnode, run=run)
        if new.configure():
            node = self._get_last_node(node)

            self.pipeline.add_after(node, new)
            if new.use_save_node:
                self.add_iso_evo_persist(new, run=False)

            if run:
                self.run_needed = new

    # save
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

    def run(self, state):
        self.debug('pipeline run started')
        for idx, node in enumerate(self.pipeline.nodes):
            action = 'skip'
            if node.enabled:
                action = 'run'
                node.run(state)
            self.debug('{} node {:02n}: {}'.format(action, idx, node.name))

        self.debug('pipeline run finished')

        # self.unknowns = state.unknowns
        # self.references = state.references

    def post_run(self, state):
        self.debug('pipeline run started')
        for idx, node in enumerate(self.pipeline.nodes):
            action = 'skip'
            if node.enabled:
                action = 'post run'
                node.post_run(state)
            self.debug('{} node {:02n}: {}'.format(action, idx, node.name))
        self.debug('pipeline run finished')

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


    def _load_predefined_templates(self):
        templates = []
        for temp in list_directory2(paths.pipeline_template_dir, extension='.yaml',
                                    remove_extension=True):
            templates.append(temp)

        self.available_pipeline_templates = templates

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
            self.unknowns = new.editor.analyses
            self.task.activate_editor(new.editor)

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



