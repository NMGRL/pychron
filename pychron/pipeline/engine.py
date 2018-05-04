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
from traits.api import HasTraits, Str, Instance, List, Event, on_trait_change, Any, Bool

import os
import time
import yaml

from pychron.core.confirmation import remember_confirmation_dialog
from pychron.core.helpers.filetools import list_directory2, add_extension
from pychron.dvc.tasks.repo_task import RepoItem
from pychron.loggable import Loggable
from pychron.paths import paths
from pychron.pipeline.nodes import FindReferencesNode
from pychron.pipeline.nodes import PushNode
from pychron.pipeline.nodes import ReviewNode
from pychron.pipeline.nodes.base import BaseNode
from pychron.pipeline.nodes.data import UnknownNode, ReferenceNode, InterpretedAgeNode
from pychron.pipeline.nodes.figure import IdeogramNode, SpectrumNode, FigureNode, SeriesNode, NoAnalysesError, \
    InverseIsochronNode
from pychron.pipeline.nodes.filter import FilterNode
from pychron.pipeline.nodes.fit import FitIsotopeEvolutionNode, FitBlanksNode, FitICFactorNode, FitFluxNode
from pychron.pipeline.nodes.grouping import GroupingNode, GraphGroupingNode, SubGroupingNode
from pychron.pipeline.nodes.persist import PDFFigureNode, IsotopeEvolutionPersistNode, \
    BlanksPersistNode, ICFactorPersistNode, FluxPersistNode, SetInterpretedAgeNode
from pychron.pipeline.pipeline_defaults import ISOEVO, BLANKS, ICFACTOR, IDEO, SPEC, SERIES, INVERSE_ISOCHRON, FLUX, \
    CSV_IDEO, XY_SCATTER, INTERPRETED_AGE_IDEOGRAM, ANALYSIS_TABLE, INTERPRETED_AGE_TABLE, AUTO_IDEOGRAM, AUTO_SERIES, \
    AUTO_REPORT, REPORT, CORRECTION_FACTORS, ANALYSIS_METADATA, REGRESSION_SERIES, GEOCHRON, VERTICAL_FLUX, \
    CSV_ANALYSES_EXPORT
from pychron.pipeline.plot.editors.figure_editor import FigureEditor
from pychron.pipeline.plot.editors.ideogram_editor import IdeogramEditor
from pychron.pipeline.plot.inspector_item import BaseInspectorItem
from pychron.pipeline.state import EngineState, get_detector_set
from pychron.pipeline.template import PipelineTemplate, PipelineTemplateSaveView, PipelineTemplateGroup, \
    PipelineTemplateRoot


class ActiveCTX(object):
    def __init__(self, node):
        self._node = node

    def __enter__(self):
        self._node.active = True

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._node.active = False
        self._node = None


class NodeGroup(BaseNode):
    nodes = List
    name = Str
    skip_configure = True

    def add_node(self, node):
        self.nodes.append(node)

    def reset(self):
        for ni in self.nodes:
            ni.reset()

    def run(self, state):
        pass


class Pipeline(HasTraits):
    name = Str('Pipeline 1')
    nodes = List
    active = Bool(False)

    def group_nodes(self):
        pass

    def add_group(self, name):
        g = NodeGroup(name=name)
        self.nodes.append(g)
        return g

    def add_node(self, node):
        self.nodes.append(node)

    def reset(self, clear_data=False):
        for ni in self.nodes:
            if isinstance(ni, UnknownNode) and clear_data:
                ni.clear_data()

            ni.reset()
        self.active = False

    # @on_trait_change('nodes[]')
    # def _handle_nodes_changed(self):
    #     for i, ni in enumerate(self.nodes):
    #         for na, nb in ((FitICFactorNode, ICFactorPersistNode),
    #                        (FitBlanksNode, BlanksPersistNode),
    #                        (FitIsotopeEvolutionNode, IsotopeEvolutionPersistNode),
    #                        (FitFluxNode, FluxPersistNode)):
    #             if isinstance(ni, na):
    #                 for nj in self.nodes[i + 1:]:
    #                     if isinstance(nj, nb):
    #                         ni.has_save_node = True

    def get_experiment_ids(self):
        ps = set()
        for node in self.nodes:
            if isinstance(node, UnknownNode):
                ps = ps.union({ai.repository_identifier for ai in node.unknowns})
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
        required = [r for ni in self.nodes for r in ni.required]

        return {'required': required, 'nodes': nodes}

    def iternodes(self, start_node=None, run_to=None):
        if run_to:
            return self.nodes[:self.nodes.index(run_to) + 1]
        else:
            if start_node is None:
                idx = -1
            else:
                idx = self.nodes.index(start_node)

            try:
                def gen():
                    for n in self.nodes[idx + 1:]:
                        yield n
                        if isinstance(n, NodeGroup):
                            for nn in n.nodes:
                                yield nn

                return list(gen())

            except IndexError:
                return []


class PipelineGroup(HasTraits):
    pipelines = List
    count = 1

    def add(self):
        self.count += 1
        p = Pipeline(name='Pipeline {}'.format(self.count))
        self.pipelines.append(p)
        return p

    def remove(self, idx):
        self.pipelines.pop(idx)

    def get_pipeline_by_node(self, node):
        return next((p for p in self.pipelines if node in p.nodes), None)

    def _pipelines_default(self):
        return [Pipeline()]


class PipelineEngine(Loggable):
    dvc = Instance('pychron.dvc.dvc.DVC')
    browser_model = Instance('pychron.envisage.browser.base_browser_model.BaseBrowserModel')
    interpreted_age_browser_model = Instance('pychron.envisage.browser.base_browser_model.BaseBrowserModel')
    pipeline = Instance(Pipeline)
    pipeline_group = Instance(PipelineGroup, ())

    selected = Any
    selected_node = Instance(BaseNode, ())

    dclicked = Event
    active_editor = Event
    active_inspector_item = Instance(BaseInspectorItem, ())
    selected_editor = Any

    resume_enabled = Bool(False)
    run_enabled = Bool(True)

    # unknowns = List
    # references = List
    add_pipeline = Event
    run_needed = Event
    refresh_all_needed = Event
    update_needed = Event
    refresh_table_needed = Event

    repositories = List
    selected_repositories = List
    # show_group_colors = Bool

    selected_pipeline_template = Any
    # available_pipeline_templates = List

    selected_unknowns = List
    selected_references = List
    dclicked_unknowns = Event
    dclicked_references = Event

    recall_analyses_needed = Event
    reset_event = Event

    tag_event = Event
    invalid_event = Event
    recall_event = Event
    omit_event = Event

    state = Instance(EngineState)
    editors = List

    pipeline_template_root = Instance(PipelineTemplateRoot)

    def __init__(self, *args, **kw):
        super(PipelineEngine, self).__init__(*args, **kw)
        self._confirmation_cache = {}

        self._load_predefined_templates()

    def drop_factory(self, items):

        return self.dvc.make_analyses(items)

    def reset(self):
        # for ni in self.pipeline.nodes:
        #     ni.visited = False
        if self.state:
            self.state.canceled = False

        self.pipeline.reset(clear_data=True)
        self.update_needed = True

    # def update_detectors(self):
    #     """
    #     set valid detectors for FitICFactorNodes
    #
    #     """
    #     if self.state:
    #         for p in self.pipeline.nodes:
    #             if isinstance(p, FitICFactorNode):
    #                 # udets = {iso.detector for ai in self.state.unknowns
    #                 #          for iso in six.itervalues(ai.isotopes)}
    #                 # udets = get_detector_set(self.state.unknowns)
    #                 # rdets = get_detector_set(self.state.references)
    #
    #                 # rdets = {iso.detector for ai in self.state.references
    #                 #          for iso in six.itervalues(ai.isotopes)}
    #                 # p.set_detectors(list(udets.union(rdets)))
    #                 p.set_detectors(self.state.union_detectors)

    def get_unknowns_node(self):
        nodes = self.get_nodes(UnknownNode)
        if nodes:
            return nodes[0]

    def get_nodes(self, klass):
        return [n for n in self.pipeline.nodes if n.__class__ == klass]

    def save_analysis_group(self):
        self.debug('save analysis group')

        from pychron.envisage.browser.add_analysis_group_view import AddAnalysisGroupView

        ans = self.selected_unknowns
        if not ans:
            ans = self.selected_node.unknowns
        projects = {a.project for a in ans}
        agv = AddAnalysisGroupView(projects={p: '{:05n}:{}'.format(i, p) for i, p in enumerate(projects)})

        project = tuple({a.project for a in ans})[0]
        agv.project = project

        info = agv.edit_traits(kind='livemodal')
        if info.result:
            agv.save(ans, self.dvc)

    def unknowns_clear_all_grouping(self):
        self._set_grouping(self.selected.unknowns, 0)

    def unknowns_clear_grouping(self):
        items = self.selected_unknowns
        if not items:
            items = self.selected.unknowns

        self._set_grouping(items, 0)

    def unknowns_graph_group_by_selected(self):
        items = self.selected.unknowns
        max_gid = max([si.graph_id for si in items]) + 1

        self._set_grouping(self.selected_unknowns, max_gid, attr='graph_id')

    def unknowns_group_by_selected(self):
        items = self.selected.unknowns
        max_gid = max([si.group_id for si in items]) + 1

        self._set_grouping(self.selected_unknowns, max_gid)

    def recall_unknowns(self):
        self.debug('recall unks')
        self.recall_analyses_needed = self.selected_unknowns

    def recall_references(self):
        self.debug('recall refs')
        self.recall_analyses_needed = self.selected_references

    def review_node(self, node):
        node.reset()
        # self.run_needed = True
        # if node.review():
        #     self.run_needed = True

    def configure(self, node):
        if not isinstance(node, BaseNode):
            return

        if node.configure():
            if isinstance(node, IdeogramNode):
                e = node.editor
                es = [ei for ei in self.editors if isinstance(ei, IdeogramEditor) and ei != node.editor]
                if es:
                    memory = self._confirmation_cache.get('Ideogram', None)
                    if memory is None:
                        yes, remember = remember_confirmation_dialog(
                            'Would you like to apply these changes to all open '
                            'Ideograms?')

                    if yes:
                        for ni in es:
                            ni.plotter_options = e.plotter_options
                            ni.refresh_needed = True

                    if remember:
                        self._confirmation_cache['Ideogram'] = yes

            osel = self.selected
            self.update_needed = True
            self.selected = osel

    def remove_node(self, node):
        try:
            self.pipeline.nodes.remove(node)
        except ValueError:
            for ni in self.pipeline.nodes:
                if isinstance(ni, NodeGroup):
                    ni.nodes.remove(node)
                    break

                    # self.run_needed = True

    def set_template(self, name):
        self.debug('Set template "{}"'.format(name))
        self._set_template(name)

    def get_experiment_ids(self):
        return self.pipeline.get_experiment_ids()

    def set_review_permanent(self, state):
        name = self.selected_pipeline_template
        path, is_user_path = self._get_template_path(name)
        if path:
            with open(path, 'r') as rfile:
                nodes = yaml.load(rfile)

            for i, ni in enumerate(nodes):
                klass = ni['klass']
                if klass == 'ReviewNode':
                    ni['enabled'] = state

            with open(path, 'w') as wfile:
                yaml.dump(nodes, wfile)

            if is_user_path:
                with open(path, 'r') as rfile:
                    paths.update_manifest(name, rfile.read())

    # debugging
    def select_default(self):
        node = self.pipeline.nodes[0]

        self.browser_model.select_project('J-Curve')
        self.browser_model.select_repository('Irradiation-NM-272')
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
        self._add_node(node, newnode, run)

    def add_references(self, node=None, run=False):
        newnode = ReferenceNode(name='references', dvc=self.dvc, browser_model=self.browser_model)
        self._add_node(node, newnode, run)

    def add_interpreted_ages(self, node, run=False):
        newnode = InterpretedAgeNode(dvc=self.dvc, browser_model=self.interpreted_age_browser_model)
        self._add_node(node, newnode, run)

    def add_review(self, node=None, run=False):
        newnode = ReviewNode()
        self._add_node(node, newnode, run)

    def chain_ideogram(self, node):
        group = self.pipeline.add_group('Ideo Group')

        n = GroupingNode()
        n.finish_load()
        group.add_node(n)

        n = IdeogramNode()
        n.finish_load()
        group.add_node(n)

    def chain_spectrum(self, node):
        pass
        # self._set_template('spectrum', clear=False, exclude_klass=['UnknownsNode'])

    def chain_blanks(self, node):
        pass
        # self._set_template('blanks', clear=False, exclude_klass=['UnknownsNode'])

    def chain_icfactors(self, node):
        pass
        # self._set_template('icfactors', clear=False, exclude_klass=['UnknownsNode'])

    def chain_isotope_evolution(self, node):
        pass
        # self._set_template('isotope_evolution', clear=False, exclude_klass=['UnknownsNode'])

    # preprocess
    def add_filter(self, node=None, run=True):
        newnode = FilterNode()
        self._add_node(node, newnode, run)

    def add_graph_grouping(self, node=None, run=True):
        newnode = GraphGroupingNode()
        self._add_node(node, newnode, run)

    def add_grouping(self, node=None, run=True):
        newnode = GroupingNode()
        self._add_node(node, newnode, run)

    def add_subgrouping(self, node=None, run=True):
        newnode = SubGroupingNode()
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

    def add_inverse_isochron(self, node=None):
        isonode = InverseIsochronNode()
        self._add_node(node, isonode)

    # fits
    def add_icfactor(self, node=None, run=True):
        new = FitICFactorNode()
        if new.configure():
            node = self._get_last_node(node)
            self.pipeline.add_after(node, new)
            if new.use_save_node:
                self.add_icfactor_persist(new, run=False)
                # if run:
                #     self.run_needed = True

    def add_blanks(self, node=None, run=True):
        new = FitBlanksNode()
        if new.configure():
            node = self._get_last_node(node)
            self.pipeline.add_after(node, new)
            if new.use_save_node:
                self.add_blanks_persist(new, run=False)
                # if run:
                #     self.run_needed = True

    def add_isotope_evolution(self, node=None, run=True):
        new = FitIsotopeEvolutionNode()
        if new.configure():
            node = self._get_last_node(node)

            self.pipeline.add_after(node, new)
            if new.use_save_node:
                self.add_iso_evo_persist(new, run=False)

                # if run:
                #     self.run_needed = new

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

    def add_push(self, node=None, run=True):
        newnode = PushNode()
        self._add_node(node, newnode, run=run)

    def add_set_interpreted_age(self, node=None, run=True):
        newnode = SetInterpretedAgeNode()
        self._add_node(node, newnode, run=run)

    # ============================================================================================================
    def save_pipeline_template(self):
        # self.info('Saving pipeline to {}'.format(path))
        v = PipelineTemplateSaveView()
        info = v.edit_traits()
        if info.result and v.path:
            path = add_extension(v.path, '.yaml')
            with open(path, 'w') as wfile:
                obj = self.pipeline.to_template()
                yaml.dump(obj, wfile, default_flow_style=False)
            self._load_predefined_templates()
            self.selected_pipeline_template = v.name

    # def run_persist(self, state):
    #     for node in self.pipeline.iternodes():
    #         if not isinstance(node, (FitNode, PersistNode)):
    #             continue
    #
    #         node.run(state)
    #         if state.canceled:
    #             self.debug('pipeline canceled by {}'.format(node))
    #             return True
    def pre_run_check(self, run_kind):
        if self.pipeline:
            ret = bool(self.pipeline.nodes)
            if not ret:
                self.warning_dialog('Please select a pipeline template to run')
            elif run_kind == 'run_from_pipeline':
                if self.selected is None or self.selected not in self.pipeline.nodes:
                    self.warning_dialog('Please select the starting node')
                    ret = False

            return ret

    def run_from_pipeline(self):
        if not self.state:
            ret = self.run_pipeline()
        else:
            node = self.selected
            idx = self.pipeline.nodes.index(node)
            idx = max(0, idx - 1)
            node = self.pipeline.nodes[idx]

            ret = self.run_pipeline(run_from=node, state=self.state)
        return ret

    def resume_pipeline(self):
        return self.run_pipeline(state=self.state)

    def refresh_figure_editors(self):
        for ed in self.state.editors:
            if isinstance(ed, FigureEditor):
                ed.refresh_needed = True

    def rerun_with(self, unks, post_run=True):
        if not self.state:
            return

        state = self.state
        state.unknowns = unks

        state.canceled = False

        ost = time.time()
        for idx, node in enumerate(self.pipeline.iternodes(None)):
            if node.enabled:
                with ActiveCTX(node):
                    # node.unknowns = []

                    if not node.pre_run(state, configure=False):
                        self.debug('Pre run failed {}'.format(node))
                        return True

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
            if post_run:
                self.post_run(state)
            return True

    def run_pipeline(self, run_from=None, state=None, pipeline=None, post_run=True):
        if pipeline is None:
            pipeline = self.pipeline

        if state is None:
            state = EngineState()
            self.state = state

        ost = time.time()

        self.dvc.create_session(force=True)

        start_node = run_from or state.veto
        self.debug('pipeline run started')
        if start_node:
            self.debug('starting at node {} {}'.format(start_node, run_from))
        state.veto = None
        state.canceled = False

        for idx, node in enumerate(pipeline.iternodes(start_node)):
            node.visited = False
            node.index = idx

        for idx, node in enumerate(pipeline.iternodes(start_node)):

            if node.enabled:
                node.editor = None

                with ActiveCTX(node):
                    if not node.pre_run(state):
                        self.debug('Pre run failed {}'.format(node))
                        return True

                    st = time.time()
                    try:
                        node.run(state)
                        node.visited = True
                        self.selected = node
                        # self.update_detectors()
                    except NoAnalysesError:
                        self.information_dialog('No Analyses in Pipeline!')
                        pipeline.reset()
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
            if post_run:
                self.post_run(state)

            # self.state = None
            return True

    run = run_pipeline

    def post_run(self, state):
        self.debug('pipeline post run started')
        for idx, node in enumerate(self.pipeline.nodes):
            action = 'skip'
            if node.enabled:
                action = 'post run'
                node.post_run(self, state)

            self.debug('{} node {:02n}: {}'.format(action, idx, node.name))
        self.debug('pipeline post run finished')
        self.post_run_refresh(state)

    def post_run_refresh(self, state=None):
        if state is None:
            state = self.state

        self.update_needed = True
        self.refresh_table_needed = True

        reponames = list({a.repository_identifier for items in (state.unknowns, state.references) for a in items})
        # print reponames
        # if self.repositories:
        #     enames = [r.name for r in self.repositories]
        #     reponames = [n for n in reponames if n not in enames]

        if reponames:
            repos = [RepoItem(name=n) for n in reponames]
            self.repositories = repos
            self._update_repository_status()

    def select_node_by_editor(self, editor):
        for node in self.pipeline.nodes:
            if hasattr(node, 'editor'):
                if node.editor == editor:
                    # print 'selecting',node
                    self.selected = node
                    # self.unknowns = editor.analyses
                    # self.refresh_table_needed = True
                    break

    def refresh_repository_status(self):
        self.debug('PipelineEngine.refresh_repository_status')
        for r in self._active_repositories():
            r.update()

    def pull(self):
        self.debug('PipelineEngine.pull')
        dvc = self.dvc
        for r in self._active_repositories():
            dvc.pull_repository(r.name)

    def push(self):
        self.debug('PipelineEngine.push')
        dvc = self.dvc
        for r in self._active_repositories():
            r.update()
            if r.behind:
                self.warning_dialog('{} is Behind and needs to be updated before it can be pushed'.format(r.name))
            else:
                dvc.push_repository(r.name)

    # private
    def _active_repositories(self):
        if self.selected_repositories:
            repos = self.selected_repositories
        else:
            repos = self.repositories
        return repos

    def _update_repository_status(self):
        for r in self.repositories:
            r.update()

    def _set_grouping(self, items, gid, attr='group_id'):
        for si in items:
            setattr(si, attr, gid)
            # si.group_id = gid

        if hasattr(self.selected, 'editor') and self.selected.editor:
            self.selected.editor.refresh_needed = True
        self.refresh_table_needed = True

    def _set_template(self, name, clear=True, exclude_klass=None):
        if isinstance(name, str):
            pt = self.pipeline_template_root.get_template(name)
        else:
            pt = name

        try:
            pt.render(self.application, self.pipeline,
                      self.browser_model,
                      self.interpreted_age_browser_model,
                      self.dvc,
                      clear=clear,
                      exclude_klass=exclude_klass)
        except BaseException as e:
            import traceback
            traceback.print_exc()
            self.debug('Invalid Template: {}'.format(e))
            self.warning_dialog('Invalid Pipeline Template. There is a syntax problem with "{}"'.format(name))
            return

        # self.update_detectors()
        if self.pipeline.nodes:
            self.selected = self.pipeline.nodes[0]

    def _get_template_path(self, name):
        pname = name.replace(' ', '_').lower()
        if pname == 'iso_evo':
            pname = 'isotope_evolutions'

        pname = add_extension(pname, '.yaml')
        path = os.path.join(paths.pipeline_template_dir, pname)
        user_path = False
        if not os.path.isfile(path):
            path = os.path.join(paths.user_pipeline_template_dir, pname)
            user_path = True
            if not os.path.isfile(path):
                self.warning_dialog('Invalid template name "{}". {} does not exist'.format(name, path))
                return

        return path, user_path

    def _load_predefined_templates(self):
        self.debug('load predefined templates')

        root = PipelineTemplateRoot()
        self.pipeline_template_root = root

        groups = []
        for name, gs in (('Fit', (('Iso Evo', ISOEVO),
                                  ('Blanks', BLANKS),
                                  ('IC Factor', ICFACTOR),
                                  ('Flux', FLUX),
                                  ('Correction Factors', CORRECTION_FACTORS))),
                         ('Plot', (('Ideogram', IDEO),
                                   ('CSV Ideogram', CSV_IDEO),
                                   ('Interpreted Age Ideogram', INTERPRETED_AGE_IDEOGRAM),
                                   ('Spectrum', SPEC),
                                   ('Series', SERIES),
                                   ('InverseIsochron', INVERSE_ISOCHRON),
                                   ('XY Scatter', XY_SCATTER),
                                   ('Regresssion', REGRESSION_SERIES),
                                   ('Vertical Flux', VERTICAL_FLUX))),
                         ('Table', (('Analysis', ANALYSIS_TABLE),
                                    ('Interpreted Age', INTERPRETED_AGE_TABLE),
                                    ('Report', REPORT))),
                         ('Auto', (('Ideogram', AUTO_IDEOGRAM),
                                   ('Series', AUTO_SERIES),
                                   ('Report', AUTO_REPORT))),
                         # ('Edit', (('Analysis Metadata', ANALYSIS_METADATA),)),
                         ('Share', (('Geochron', GEOCHRON),
                                    ('CSV Analyses Export', CSV_ANALYSES_EXPORT)))

                         ):
            grp = PipelineTemplateGroup(name=name)
            grp.templates = [PipelineTemplate(n, t) for n, t in gs]
            groups.append(grp)

        grp = PipelineTemplateGroup(name='User')
        user_templates = []
        for temp in list_directory2(paths.user_pipeline_template_dir, extension='.yaml',
                                    remove_extension=True):
            user_templates.append(PipelineTemplate(temp, os.path.join(paths.user_pipeline_template_dir,
                                                                      '{}.yaml'.format(temp))))

        grp.templates = user_templates
        groups.append(grp)

        self.debug('loaded {} user templates'.format(len(user_templates)))

        root.groups = groups

    def _add_find_node(self, node, run, analysis_type):
        newnode = FindReferencesNode(dvc=self.dvc, analysis_type=analysis_type)
        if newnode.configure():
            node = self._get_last_node(node)

            self.pipeline.add_after(node, newnode)
            self.add_references(newnode, run=False)

            if run:
                self.run_needed = newnode

    def _add_node(self, node, new, run=True):
        # if new.configure():
        node = self._get_last_node(node)
        self.pipeline.add_after(node, new)
        # if run:
        #     self.run_needed = new

    def _get_last_node(self, node=None):
        if node is None:
            if self.pipeline.nodes:
                idx = len(self.pipeline.nodes) - 1

                node = self.pipeline.nodes[idx]
        return node

    # handlers
    @on_trait_change('active_editor')
    def _handle_active_editor(self, obj, name, old, new):
        def refresh():
            self.refresh_table_needed = True

        if old:
            if hasattr(old, 'figure_model'):
                old.on_trait_change(refresh, 'figure_model:panels:figures:refresh_unknowns_table', remove=True)

        if new:
            if hasattr(new, 'figure_model'):
                new.on_trait_change(refresh, 'figure_model:panels:figures:refresh_unknowns_table')

    def _add_pipeline_fired(self):
        p = self.pipeline_group.add()
        self.pipeline = p
        self.selected_pipeline_template = ''

    def _dclicked_unknowns_changed(self):
        if self.selected_unknowns:
            self.recall_unknowns()

    def _dclicked_references_fired(self):
        if self.selected_references:
            self.recall_references()

    def _selected_pipeline_template_changed(self, new):
        if isinstance(new, PipelineTemplate) or isinstance(new, str):
            if self.run_enabled and not self.pipeline.active:
                self.debug('Pipeline template {} selected'.format(new))
                self._set_template(new)

    def _selected_changed(self, old, new):
        if isinstance(new, Pipeline):
            self.pipeline = new
        elif isinstance(new, NodeGroup):
            pass
        else:
            self.selected_node = new
            if old:
                old.on_trait_change(self._handle_tag, 'unknowns:tag_event,references:tag_event', remove=True)
                old.on_trait_change(self._handle_invalid, 'unknowns:invalid_event,references:invalid_event',
                                    remove=True)
                old.on_trait_change(self._handle_omit, 'unknowns:omit_event,references:omit_event', remove=True)
                old.on_trait_change(self._handle_recall, 'unknowns:recall_event,references:recall_event', remove=True)
                old.on_trait_change(self._handle_len_unknowns, 'unknowns_items', remove=True)
                old.on_trait_change(self._handle_len_references, 'references_items', remove=True)
                old.on_trait_change(self._handle_status, 'unknowns:temp_status,references:temp_status', remove=True)

            if new:
                new.on_trait_change(self._handle_tag, 'unknowns:tag_event,references:tag_event')
                new.on_trait_change(self._handle_invalid, 'unknowns:invalid_event,references:invalid_event')
                new.on_trait_change(self._handle_omit, 'unknowns:omit_event,references:omit_event')
                new.on_trait_change(self._handle_recall, 'unknowns:recall_event,references:recall_event')
                new.on_trait_change(self._handle_status, 'unknowns:temp_status,references:temp_status')
                new.on_trait_change(self._handle_len_unknowns, 'unknowns_items')
                new.on_trait_change(self._handle_len_references, 'references_items')

            if isinstance(new, FigureNode):
                if new.editor:
                    editor = new.editor
                    self.selected_editor = editor
                    self.active_editor = editor

    def refresh_unknowns(self, unks, refresh_editor=False):
        self.selected.unknowns = unks
        self.selected.editor.set_items(unks, refresh=refresh_editor)

    _len_unknowns_cnt = 0
    _len_unknowns_removed = 0
    _len_references_cnt = 0
    _len_references_removed = 0

    def _handle_len_unknowns(self, new):
        self._handle_len('unknowns', lambda e: e.set_items(self.selected.unknowns))

        def func(editor):
            vs = self.selected.unknowns
            editor.set_items(vs)
            self.state.unknowns = vs
            for node in self.pipeline.nodes:
                if isinstance(node, UnknownNode) and node is not self.selected:
                    node.unknowns = vs

        self._handle_len('unknowns', func)

    def _handle_len_references(self, new):
        def func(editor):
            vs = self.selected.references
            editor.set_references(vs)
            self.state.references = vs

            for node in self.pipeline.nodes:
                if isinstance(node, ReferenceNode) and node is not self.selected:
                    node.references = vs

        self._handle_len('references', func)

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

    def _handle_status(self, new):
        self.refresh_table_needed = True

    def _handle_recall(self, new):
        self.recall_event = new

    def _handle_tag(self, new):
        self.tag_event = new

    def _handle_invalid(self, new):
        self.invalid_event = new

    def _handle_omit(self, new):
        self.omit_event = new

    def _dclicked_changed(self, new):
        self.configure(new)

    def _pipeline_default(self):
        return self.pipeline_group.pipelines[0]

# ============= EOF =============================================
