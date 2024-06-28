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

import os
import time
from operator import attrgetter, itemgetter

import yaml

# ============= enthought library imports =======================
from apptools.preferences.preference_binding import bind_preference
from pyface.timer.do_later import do_later
from traits.api import (
    HasTraits,
    Str,
    Instance,
    List,
    Event,
    on_trait_change,
    Any,
    Bool,
    Dict,
)

from pychron.core.confirmation import remember_confirmation_dialog
from pychron.core.helpers.filetools import glob_list_directory, add_extension
from pychron.core.helpers.iterfuncs import groupby_key
from pychron.core.yaml import yload
from pychron.dvc.tasks.repo_task import RepoItem
from pychron.envisage.resources import icon
from pychron.envisage.view_util import open_view
from pychron.globals import globalv
from pychron.loggable import Loggable
from pychron.paths import paths
from pychron.pipeline.grouping import group_analyses_by_key
from pychron.pipeline.nodes import FindReferencesNode, AuditNode
from pychron.pipeline.nodes import PushNode
from pychron.pipeline.nodes import ReviewNode
from pychron.pipeline.nodes.base import BaseNode
from pychron.pipeline.nodes.data import UnknownNode, ReferenceNode, InterpretedAgeNode
from pychron.pipeline.nodes.figure import (
    IdeogramNode,
    SpectrumNode,
    SeriesNode,
    NoAnalysesError,
    InverseIsochronNode,
)
from pychron.pipeline.nodes.filter import FilterNode, MSWDFilterNode
from pychron.pipeline.nodes.fit import (
    FitIsotopeEvolutionNode,
    FitBlanksNode,
    FitICFactorNode,
)
from pychron.pipeline.nodes.grouping import (
    GroupingNode,
    GraphGroupingNode,
    SubGroupingNode,
)
from pychron.pipeline.nodes.ia import SetInterpretedAgeNode
from pychron.pipeline.nodes.persist import (
    PDFFigureNode,
    IsotopeEvolutionPersistNode,
    BlanksPersistNode,
    ICFactorPersistNode,
)
from pychron.pipeline.pipeline_defaults import (
    ISOEVO,
    BLANKS,
    ICFACTOR,
    IDEO,
    SPEC,
    SERIES,
    INVERSE_ISOCHRON,
    FLUX,
    CSV_IDEO,
    XY_SCATTER,
    INTERPRETED_AGE_IDEOGRAM,
    ANALYSIS_TABLE,
    INTERPRETED_AGE_TABLE,
    REPORT,
    REGRESSION_SERIES,
    VERTICAL_FLUX,
    CSV_ANALYSES_EXPORT,
    BULK_EDIT,
    HISTORY_IDEOGRAM,
    HISTORY_SPECTRUM,
    AUDIT,
    SUBGROUP_IDEOGRAM,
    HYBRID_IDEOGRAM,
    MASSSPEC_REDUCED,
    DEFINE_EQUILIBRATION,
    CA_CORRECTION_FACTORS,
    K_CORRECTION_FACTORS,
    FLUX_VISUALIZATION,
    CSV_RAW_DATA_EXPORT,
    COMPOSITE,
    SIMPLE_ANALYSIS_TABLE,
    MASS_SPEC_FLUX,
    PYSCRIPT,
    RATIO_SERIES,
    CSV_SPEC,
    ARAR_IDEO,
    ARAR_SPEC,
    ARAR_INVERSE_ISOCHRON,
    ARAR_SIMPLE_ANALYSIS_TABLE,
    RUNID_EDIT,
    CORRELATION_IDEO,
    COSMOGENIC,
    FLUX_EXPORT,
    RECENT_RUNS,
    CSV_INVERSE_ISOCHRON,
    CSV_REGRESSION,
    REVERT_HISTORY,
)
from pychron.pipeline.plot.editors.figure_editor import FigureEditor
from pychron.pipeline.plot.editors.ideogram_editor import IdeogramEditor
from pychron.pipeline.plot.editors.spectrum_editor import SpectrumEditor
from pychron.pipeline.state import EngineState
from pychron.pipeline.template import (
    PipelineTemplate,
    PipelineTemplateSaveView,
    PipelineTemplateGroup,
    PipelineTemplateRoot,
)
from pychron.pychron_constants import BLANK_UNKNOWN, AIR, DEFAULT_PIPELINE_ROOTS


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
    name = Str("Pipeline 1")
    nodes = List
    active = Bool(False)

    def resume(self, state):
        start_node = state.veto

        idx = self.nodes.index(start_node)
        try:
            prev_node = self.nodes[idx - 1]
        except IndexError:
            return

        prev_node.resume(state)

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

        return {"required": required, "nodes": nodes}

    def iternodes(self, start_node=None, run_to=None):
        if run_to:
            return self.nodes[: self.nodes.index(run_to) + 1]
        else:
            if start_node is None:
                idx = -1
            else:
                idx = self.nodes.index(start_node)

            try:

                def gen():
                    for n in self.nodes[idx + 1 :]:
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
        p = Pipeline(name="Pipeline {}".format(self.count))
        self.pipelines.append(p)
        return p

    def remove(self, idx):
        self.pipelines.pop(idx)

    def get_pipeline_by_node(self, node):
        return next((p for p in self.pipelines if node in p.nodes), None)

    def _pipelines_default(self):
        return [Pipeline()]


class PipelineEngine(Loggable):
    dvc = Instance("pychron.dvc.dvc.DVC")
    browser_model = Instance(
        "pychron.envisage.browser.base_browser_model.BaseBrowserModel"
    )
    interpreted_age_browser_model = Instance(
        "pychron.envisage.browser.base_browser_model.BaseBrowserModel"
    )
    pipeline = Instance(Pipeline)
    pipeline_group = Instance(PipelineGroup, ())
    nodes = List
    node_factories = List
    predefined_templates = (
        List  # contributed to by other plugins. passed in by PipelinePlugin
    )
    pipeline_group_icon_map = (
        Dict  # contributed to by other plugins. passed in by PipelinePlugin
    )

    selected = Instance(BaseNode, ())

    dclicked = Event
    active_editor = Event
    selected_editor = Any

    resume_enabled = Bool(False)
    run_enabled = Bool(True)

    add_pipeline = Event
    run_needed = Event
    refresh_all_needed = Event
    update_needed = Event
    refresh_table_needed = Event
    tag_event = Event

    repositories = List
    selected_repositories = List

    selected_pipeline_template = Any
    dclicked_pipeline_template = Event

    selected_unknowns = List
    selected_references = List
    dclicked_unknowns = Event
    dclicked_references = Event

    recall_analyses_needed = Event
    play_analysis_video_needed = Event
    reset_event = Event

    state = Instance(EngineState)
    editors = List

    pipeline_template_root = Instance(PipelineTemplateRoot)
    use_arar_calculations = Bool

    def __init__(self, *args, **kw):
        super(PipelineEngine, self).__init__(*args, **kw)
        self._confirmation_cache = {}
        bind_preference(
            self, "use_arar_calculations", "pychron.pipeline.use_arar_calculations"
        )

    def drop_factory(self, items):
        return self.dvc.make_analyses(items)

    def reset(self):
        if self.state:
            self.state.canceled = False

        self.pipeline.reset(clear_data=True)
        self.update_needed = True

    def get_unknowns_node(self):
        nodes = self.get_nodes(UnknownNode)
        if nodes:
            return nodes[0]

    def get_nodes(self, klass):
        return [n for n in self.pipeline.nodes if n.__class__ == klass]

    def save_analysis_group(self):
        self.debug("save analysis group")

        from pychron.envisage.browser.add_analysis_group_view import (
            AddAnalysisGroupView,
        )

        ans = self.selected_unknowns
        if not ans:
            ans = self.selected.unknowns
        projects = {a.project for a in ans}
        agv = AddAnalysisGroupView(
            projects={p: "{:05n}:{}".format(i, p) for i, p in enumerate(projects)}
        )

        project = tuple({a.project for a in ans})[0]
        agv.project = project

        info = agv.edit_traits(kind="livemodal")
        if info.result:
            agv.save(ans, self.dvc)

    def unknowns_set_fixed_plateau(self):
        items = self.selected_unknowns
        if not items:
            items = self.selected.unknowns

        if len(items) > 1:
            s, e = items[0], items[-1]
            gs = self.selected.editor.get_analysis_groups()
            for gi in gs:
                if s in gi.analyses:
                    gi.calculate_fixed_plateau = True
                    gi.fixed_step_low = s.step
                    gi.fixed_step_high = e.step

                    self.selected.editor.figure_model.force_refresh_panels = False
                    self.selected.editor.refresh_needed = True
                    self.selected.editor.figure_model.force_refresh_panels = True
                    break

    def unknowns_clear_all_grouping(self):
        self._set_grouping(self.selected.unknowns, 0)

    def unknowns_clear_grouping(self):
        items = self.selected_unknowns
        if not items:
            items = self.selected.unknowns

        self._set_grouping(items, 0)
        self._set_grouping(items, 0, attr="aux_id")

    def unknowns_group_by(self, attr):
        items = self.selected_unknowns
        if not items or len(items) == 1:
            items = self.selected.unknowns
        group_analyses_by_key(items, attr)

        sunks = sorted(self.selected.unknowns, key=attrgetter(attr))
        self.selected.unknowns = sunks
        self.refresh_figure_editors()

    def group_selected(self, key):
        # if there are multiple graphs only get the analyses from the selected graph
        if key != "graph_id":
            # e.g. key=='group_id'
            items = self.selected_unknowns
            graph_id = items[0].graph_id
            items = [i for i in items if i.graph_id == graph_id]
            items_to_set = items
        else:
            # graph grouping
            items = self.selected.unknowns
            items_to_set = self.selected_unknowns

        max_gid = max([getattr(si, key) for si in items]) + 1
        self._set_grouping(items_to_set, max_gid, attr=key)

    def unknowns_toggle_status(self):
        for i in self.selected_unknowns:
            # print('asdf', i.temp_status)
            i.temp_status = "ok" if i.temp_status == "omit" else "omit"
            if hasattr(self.selected, "editor") and self.selected.editor:
                self.selected.editor.refresh_needed = True

    def play_analysis_video(self):
        self.debug("play analysis video")
        self.play_analysis_video_needed = self.selected_unknowns

    def recall_unknowns(self):
        self.debug("recall unks")
        self.recall_analyses_needed = self.selected_unknowns

    def recall_references(self):
        self.debug("recall refs")
        self.recall_analyses_needed = self.selected_references

    def review_node(self, node):
        node.reset()

    def configure(self, node):
        if not isinstance(node, BaseNode):
            return

        if node.configure():
            for tag, klass, editor in (
                ("Ideogram", IdeogramNode, IdeogramEditor),
                ("Spectrum", SpectrumNode, SpectrumEditor),
            ):
                if isinstance(node, klass):
                    e = node.editor
                    es = [
                        ei
                        for ei in self.editors
                        if isinstance(ei, editor) and ei != node.editor
                    ]
                    if es:
                        memory = self._confirmation_cache.get(tag, None)
                        if memory is None:
                            yes, remember = remember_confirmation_dialog(
                                "Would you like to apply these changes to all open "
                                "{}?".format(tag)
                            )

                        if yes:
                            for ni in es:
                                ni.plotter_options = e.plotter_options
                                ni.refresh_needed = True

                        if remember:
                            self._confirmation_cache[tag] = yes

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

    def set_template(self, name):
        self.debug('Set template "{}"'.format(name))
        self._set_template(name)

    def get_experiment_ids(self):
        return self.pipeline.get_experiment_ids()

    def set_review_permanent(self, state):
        name = self.selected_pipeline_template
        path, is_user_path = self._get_template_path(name)
        if path:
            nodes = yload(path)
            for i, ni in enumerate(nodes):
                klass = ni["klass"]
                if klass == "ReviewNode":
                    ni["enabled"] = state

            with open(path, "w") as wfile:
                yaml.dump(nodes, wfile)

            if is_user_path:
                with open(path, "r") as rfile:
                    paths.update_manifest(name, rfile.read())

    # debugging
    def select_default(self):
        node = self.pipeline.nodes[0]

        self.browser_model.select_project("J-Curve")
        self.browser_model.select_repository("Irradiation-NM-272")
        self.browser_model.select_sample(idx=0)
        records = self.browser_model.get_analysis_records()
        if records:
            analyses = self.dvc.make_analyses(records)
            node.unknowns.extend(analyses)
            node._manual_configured = True

    def add_test_filter(self):
        node = self.pipeline.nodes[-1]
        newnode = FilterNode()
        filt = newnode.filters[0]
        filt.attribute = "uage"
        filt.comparator = "<"
        filt.criterion = "10"

        self.pipeline.add_after(node, newnode)

    def clear(self):
        for ni in self.pipeline.nodes:
            ni.clear_data()

    def remove_invalid(self):
        unks = self.selected.unknowns
        self.selected.unknowns = [unk for unk in unks if unk.tag.lower() != "invalid"]
        self.refresh_table_needed = True
        self.state.unknowns = self.selected.unknowns

    # ============================================================================================================
    # nodes
    # ============================================================================================================
    # data

    def add_data(self, node=None):
        """

        add a default data node
        :return:
        """

        self.debug("add data node")
        newnode = UnknownNode(dvc=self.dvc, browser_model=self.browser_model)
        self._add_node(node, newnode)

    def add_references(self, node=None):
        newnode = ReferenceNode(
            name="references", dvc=self.dvc, browser_model=self.browser_model
        )
        self._add_node(node, newnode)

    def add_interpreted_ages(self, node):
        newnode = InterpretedAgeNode(
            dvc=self.dvc, browser_model=self.interpreted_age_browser_model
        )
        self._add_node(node, newnode)

    def add_review(self, node=None):
        newnode = ReviewNode()
        self._add_node(node, newnode)

    def chain_ideogram(self, node):
        group = self.pipeline.add_group("Ideo Group")

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
    def add_mswd_filter(self, node=None):
        newnode = MSWDFilterNode()
        self._add_node(node, newnode)

    def add_filter(self, node=None):
        newnode = FilterNode()
        self._add_node(node, newnode)

    def add_graph_grouping(self, node=None):
        newnode = GraphGroupingNode()
        self._add_node(node, newnode)

    def add_grouping(self, node=None):
        newnode = GroupingNode()
        self._add_node(node, newnode)

    def add_subgrouping(self, node=None):
        newnode = SubGroupingNode()
        self._add_node(node, newnode)

    # find
    def add_find_airs(self, node=None):
        self._add_find_node(node, AIR)

    def add_find_blanks(self, node=None):
        self._add_find_node(node, BLANK_UNKNOWN)

    # figures
    def add_spectrum(self, node=None):
        newnode = SpectrumNode()
        self._add_node(node, newnode)

    def add_ideogram(self, node=None):
        ideo_node = IdeogramNode()
        self._add_node(node, ideo_node)

    def add_series(self, node=None):
        series_node = SeriesNode()
        self._add_node(node, series_node)

    def add_inverse_isochron(self, node=None):
        isonode = InverseIsochronNode()
        self._add_node(node, isonode)

    # fits
    def add_icfactor(self, node=None):
        new = FitICFactorNode()
        if new.configure():
            node = self._get_last_node(node)
            self.pipeline.add_after(node, new)
            if new.use_save_node:
                self.add_icfactor_persist(new)

    def add_blanks(self, node=None):
        new = FitBlanksNode()
        if new.configure():
            node = self._get_last_node(node)
            self.pipeline.add_after(node, new)
            if new.use_save_node:
                self.add_blanks_persist(new)

    def add_isotope_evolution(self, node=None):
        new = FitIsotopeEvolutionNode()
        if new.configure():
            node = self._get_last_node(node)

            self.pipeline.add_after(node, new)
            if new.use_save_node:
                self.add_iso_evo_persist(new)

    def add_audit(self, node=None):
        new = AuditNode()
        if new.configure():
            node = self._get_last_node(node)

            self.pipeline.add_after(node, new)

    # save
    def add_icfactor_persist(self, node=None):
        new = ICFactorPersistNode(dvc=self.dvc)
        self._add_node(node, new)

    def add_blanks_persist(self, node=None):
        new = BlanksPersistNode(dvc=self.dvc)
        self._add_node(node, new)

    def add_iso_evo_persist(self, node=None):
        new = IsotopeEvolutionPersistNode(dvc=self.dvc)
        self._add_node(node, new)

    def add_pdf_figure(self, node=None):
        newnode = PDFFigureNode(root="/Users/ross/Sandbox")
        self._add_node(node, newnode)

    def add_push(self, node=None):
        newnode = PushNode()
        self._add_node(node, newnode)

    def add_set_interpreted_age(self, node=None):
        newnode = SetInterpretedAgeNode()
        self._add_node(node, newnode)

    # ============================================================================================================
    def save_pipeline_template(self):
        # self.info('Saving pipeline to {}'.format(path))
        v = PipelineTemplateSaveView()
        info = v.edit_traits()
        if info.result and v.path:
            if v.group_path:
                if not os.path.isdir(v.group_path):
                    os.mkdir(v.group_path)

            path = add_extension(v.path, ".yaml")
            with open(path, "w") as wfile:
                obj = self.pipeline.to_template()
                yaml.dump(obj, wfile, default_flow_style=False)

            self.load_predefined_templates()
            self.selected_pipeline_template = v.name

    def pre_run_check(self, run_kind):
        if self.pipeline:
            ret = bool(self.pipeline.nodes)
            if not ret:
                self.warning_dialog("Please select a pipeline template to run")
            elif run_kind == "run_from_pipeline":
                if self.selected is None or self.selected not in self.pipeline.nodes:
                    self.warning_dialog("Please select the starting node")
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
                print("refresh figure editors")
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
                    if not node.pre_run(state, configure=False):
                        self.debug("Pre run failed {}".format(node))
                        return True

                    st = time.time()
                    try:
                        node.run(state)
                        node.visited = True
                        self.selected = node
                    except NoAnalysesError:
                        self.information_dialog("No Analyses in Pipeline!")
                        self.pipeline.reset()
                        return True
                    self.debug(
                        "{:02n}: {} Runtime: {:0.4f}".format(
                            idx, node, time.time() - st
                        )
                    )

                    if state.veto:
                        self.debug("pipeline vetoed by {}".format(node))
                        return

                    if state.canceled:
                        self.debug("pipeline canceled by {}".format(node))
                        return True

            else:
                self.debug("Skip node {:02n}: {}".format(idx, node))
        else:
            self.debug("pipeline run finished")
            self.debug("pipeline runtime {}".format(time.time() - ost))
            if post_run:
                self.post_run(state)
            return True

    def run_pipeline(
        self, run_from=None, state=None, pipeline=None, post_run=True, configure=True
    ):
        self.selected_unknowns = []
        self.selected_references = []

        if pipeline is None:
            pipeline = self.pipeline

        if state is None:
            state = EngineState()
            self.state = state
        else:
            self.debug("using existing state")

        ost = time.time()

        self.dvc.create_session(force=True)

        if state.veto:
            pipeline.resume(state)

        start_node = run_from or state.veto
        self.debug("pipeline run started")
        if start_node:
            self.debug("starting at node {} {}".format(start_node, run_from))
        state.veto = None
        state.canceled = False

        for idx, node in enumerate(pipeline.iternodes(start_node)):
            node.visited = False
            node.index = idx

        if globalv.skip_configure:
            configure = False

        for idx, node in enumerate(pipeline.iternodes(start_node)):
            if node.enabled:
                # node.editor = None

                with ActiveCTX(node):
                    if not node.pre_run(state, configure=configure):
                        self.debug("Pre run failed {}".format(node))
                        return True

                    st = time.time()
                    try:
                        node.run(state)
                        node.visited = True
                        self.selected = node
                        # self.update_detectors()
                    except NoAnalysesError:
                        self.information_dialog("No Analyses in Pipeline!")
                        pipeline.reset()
                        return True
                    self.debug(
                        "{:02n}: {} Runtime: {:0.4f}".format(
                            idx, node, time.time() - st
                        )
                    )

                    if state.veto:
                        if state.veto_message:
                            self.information_dialog(state.veto_message)

                        self.debug("pipeline vetoed by {}".format(node))
                        return

                    if state.canceled:
                        self.debug("pipeline canceled by {}".format(node))
                        return True

            else:
                self.debug("Skip node {:02n}: {}".format(idx, node))
        else:
            self.debug("pipeline run finished")
            self.debug("pipeline runtime {}".format(time.time() - ost))
            if post_run:
                self.post_run(state)

            return True

    run = run_pipeline

    def post_run(self, state):
        self.debug("pipeline post run started")
        for idx, node in enumerate(self.pipeline.nodes):
            action = "skip"
            if node.enabled:
                action = "post run"
                node.post_run(self, state)

            self.debug("{} node {:02n}: {}".format(action, idx, node.name))
        self.debug("pipeline post run finished")
        self.post_run_refresh(state)

    def post_run_refresh(self, state=None):
        if state is None:
            state = self.state

        self.update_needed = True
        self.refresh_table_needed = True

        # always select last node
        self.selected = self.pipeline.nodes[-1]

        reponames = list(
            {
                a.repository_identifier
                for items in (state.unknowns, state.references)
                for a in items
            }
        )

        if reponames:
            repos = [RepoItem(name=n) for n in reponames]
            self.repositories = repos
            self._update_repository_status()

    def select_node_by_editor(self, editor):
        for node in self.pipeline.nodes:
            if hasattr(node, "editor"):
                if node.editor == editor:
                    self.selected = node
                    break

    def refresh_repository_status(self):
        self.debug("PipelineEngine.refresh_repository_status")
        for r in self._active_repositories():
            r.update()

    def pull(self):
        self.debug("PipelineEngine.pull")
        dvc = self.dvc
        for r in self._active_repositories():
            dvc.pull_repository(r.name)

    def push(self):
        self.debug("PipelineEngine.push")
        dvc = self.dvc
        for r in self._active_repositories():
            r.update()
            if r.behind:
                self.warning_dialog(
                    "{} is Behind and needs to be updated before it can be pushed".format(
                        r.name
                    )
                )
            else:
                dvc.push_repository(r.name)

    def delete_local_changes(self):
        self.debug("PipelineEngine.delete_local_changes")
        dvc = self.dvc
        for r in self._active_repositories():
            dvc.delete_local_commits(r.name)

    def load_predefined_templates(self):
        self.debug("load predefined templates")

        root = PipelineTemplateRoot()
        nodes = {n.__name__: n for n in self.nodes}
        node_factories = {v.name: v for v in self.node_factories}
        groups = []

        if self.use_arar_calculations:
            plots = (
                ("Ideogram", ARAR_IDEO),
                ("CSV Ideogram", CSV_IDEO),
                ("Interpreted Age Ideogram", INTERPRETED_AGE_IDEOGRAM),
                ("Hybrid Ideogram", HYBRID_IDEOGRAM),
                ("SubGroup Ideogram", SUBGROUP_IDEOGRAM),
                ("Spectrum", ARAR_SPEC),
                ("CSV Spectrum", CSV_SPEC),
                ("Spectrum/Isochron", COMPOSITE),
                ("Series", SERIES),
                ("Ratio Series", RATIO_SERIES),
                ("InverseIsochron", ARAR_INVERSE_ISOCHRON),
                ("XY Scatter", XY_SCATTER),
                ("Regression", REGRESSION_SERIES),
                ("Flux Visualization", FLUX_VISUALIZATION),
                ("Vertical Flux", VERTICAL_FLUX),
            )
            tables = (
                ("SubGrouped Analyses", ANALYSIS_TABLE),
                ("Grouped Analyses", ARAR_SIMPLE_ANALYSIS_TABLE),
                ("Interpreted Age", INTERPRETED_AGE_TABLE),
                ("Report", REPORT),
            )
        else:
            plots = (
                ("Recent Recall", RECENT_RUNS),
                ("Ideogram", IDEO),
                ("Correlation Ideogram", CORRELATION_IDEO),
                ("CSV Ideogram", CSV_IDEO),
                ("Interpreted Age Ideogram", INTERPRETED_AGE_IDEOGRAM),
                ("Hybrid Ideogram", HYBRID_IDEOGRAM),
                ("SubGroup Ideogram", SUBGROUP_IDEOGRAM),
                ("Spectrum", SPEC),
                ("CSV Spectrum", CSV_SPEC),
                ("Spectrum/Isochron", COMPOSITE),
                ("Series", SERIES),
                ("Ratio Series", RATIO_SERIES),
                ("InverseIsochron", INVERSE_ISOCHRON),
                ("CSV InverseIsochron", CSV_INVERSE_ISOCHRON),
                ("XY Scatter", XY_SCATTER),
                ("CSV Regression", CSV_REGRESSION),
                ("Isotope Regression", REGRESSION_SERIES),
                ("Flux Visualization", FLUX_VISUALIZATION),
                ("Vertical Flux", VERTICAL_FLUX),
            )
            tables = (
                ("SubGrouped Analyses", ANALYSIS_TABLE),
                ("Grouped Analyses", SIMPLE_ANALYSIS_TABLE),
                ("Interpreted Age", INTERPRETED_AGE_TABLE),
                ("Report", REPORT),
            )

        default = [
            (
                "Fit",
                (
                    ("Define Equilibration", DEFINE_EQUILIBRATION),
                    ("Iso Evo", ISOEVO),
                    ("Blanks", BLANKS),
                    ("IC Factor", ICFACTOR),
                    ("Flux", FLUX),
                    ("Cosmogenic", COSMOGENIC),
                    ("Ca Correction Factors", CA_CORRECTION_FACTORS),
                    ("K Correction Factors", K_CORRECTION_FACTORS),
                    ("Audit", AUDIT),
                ),
            ),
            (
                "Edit",
                (
                    ("Bulk Edit", BULK_EDIT),
                    ("RunID Edit", RUNID_EDIT),
                    ("Revert History", REVERT_HISTORY),
                ),
            ),
            ("Plot", plots),
            ("Table", tables),
            (
                "History",
                (("Ideogram", HISTORY_IDEOGRAM), ("Spectrum", HISTORY_SPECTRUM)),
            ),
            (
                "Share",
                (
                    ("CSV Analyses Export", CSV_ANALYSES_EXPORT),
                    ("CSV Raw Data Export", CSV_RAW_DATA_EXPORT),
                    ("CSV Flux Export", FLUX_EXPORT),
                ),
            ),
            (
                "Transfer",
                (
                    ("Mass Spec Reduced", MASSSPEC_REDUCED),
                    ("Mass Spec Flux", MASS_SPEC_FLUX),
                ),
            ),
            ("Scripting", (("PyScript", PYSCRIPT),)),
        ]

        # predefined_templates contributed to by other plugins
        for grp_name, gs in groupby_key(
            default + self.predefined_templates, key=itemgetter(0)
        ):
            grp = PipelineTemplateGroup(
                name=grp_name, icon=icon(self.pipeline_group_icon_map.get(grp_name, ""))
            )

            templates = [
                PipelineTemplate(n, text, nodes, node_factories)
                for nn, gg in gs
                for n, text in gg
            ]

            pp = os.path.join(paths.user_pipeline_template_dir, grp_name.lower())
            # add templates from named user directory
            for temp in glob_list_directory(
                pp, extension=".yaml", remove_extension=True
            ):
                path = os.path.join(pp, "{}.yaml".format(temp))
                templates.append(PipelineTemplate(temp, path, nodes, node_factories))

            grp.templates = templates
            groups.append(grp)

        # add user templates from user directory
        grp = PipelineTemplateGroup(name="User", icon=icon("user_suit"))
        user_templates = []
        for temp in glob_list_directory(
            paths.user_pipeline_template_dir, extension=".yaml", remove_extension=True
        ):
            path = os.path.join(
                paths.user_pipeline_template_dir, "{}.yaml".format(temp)
            )
            user_templates.append(PipelineTemplate(temp, path, nodes, node_factories))

        grp.templates = user_templates
        groups.append(grp)

        # reorder groups
        ngroups = []
        for gi in DEFAULT_PIPELINE_ROOTS:  # ('Fit', 'Plot', 'Table',...)
            g = next((gii for gii in groups if gii.name == gi), None)
            if g is not None:
                ngroups.append(g)

        # add in groups contributed to by plugins or from users template directories
        for gi in groups:
            if gi.name not in DEFAULT_PIPELINE_ROOTS:
                ngroups.append(gi)

        self.debug("loaded {} user templates".format(len(user_templates)))

        root.groups = ngroups
        self.pipeline_template_root = root

    def refresh_unknowns(self, unks, refresh_editor=False):
        self.selected.unknowns = unks
        self.selected.editor.set_items(unks, refresh=refresh_editor)

    def handle_status(self, new):
        self.refresh_table_needed = True

    def handle_len_unknowns(self, new):
        self._handle_len("unknowns", lambda e: e.set_items(self.selected.unknowns))

        def func(editor):
            vs = self.selected.unknowns
            if editor:
                editor.set_items(vs)
            self.state.unknowns = vs
            for node in self.pipeline.nodes:
                if isinstance(node, UnknownNode) and node is not self.selected:
                    node.unknowns = vs

        self._handle_len("unknowns", func)

    def handle_len_references(self, new):
        def func(editor):
            vs = self.selected.references
            editor.set_references(vs)
            self.state.references = vs

            for node in self.pipeline.nodes:
                if isinstance(node, ReferenceNode) and node is not self.selected:
                    node.references = vs

        self._handle_len("references", func)

    def identify_peaks(self, *args, **kw):
        self._identify_peaks(*args, **kw)

    # private
    def _active_repositories(self):
        if self.selected_repositories:
            repos = self.selected_repositories
        else:
            repos = self.repositories
        return repos

    def _update_repository_status(self):
        for r in self.repositories:
            if r.name:
                if not r.update():
                    self.warning('Failed to update repo="{}"'.format(r.name))

    def _set_grouping(self, items, gid, attr="group_id"):
        for si in items:
            setattr(si, attr, gid)

        if hasattr(self.selected, "editor") and self.selected.editor:
            self.selected.editor.refresh_needed = True
        self.refresh_table_needed = True

    def _set_template(self, name, clear=True, exclude_klass=None):
        self.debug("template set to ={}".format(name))
        if isinstance(name, (str, tuple)):
            pt = self.pipeline_template_root.get_template(name)
        else:
            pt = name

        try:
            pt.render(
                self.application,
                self.pipeline,
                self.browser_model,
                self.interpreted_age_browser_model,
                self.dvc,
                clear=clear,
                exclude_klass=exclude_klass,
            )
        except BaseException as e:
            import traceback

            traceback.print_exc()
            self.debug("Invalid Template: {}".format(e))
            self.warning_dialog(
                'Invalid Pipeline Template. There is a syntax problem with "{}"'.format(
                    name
                )
            )
            return

        if self.pipeline.nodes:
            self.selected = self.pipeline.nodes[0]

    def _get_template_path(self, name):
        pname = name.replace(" ", "_").lower()
        if pname == "iso_evo":
            pname = "isotope_evolutions"

        pname = add_extension(pname, ".yaml")
        path = os.path.join(paths.pipeline_template_dir, pname)
        user_path = False
        if not os.path.isfile(path):
            path = os.path.join(paths.user_pipeline_template_dir, pname)
            user_path = True
            if not os.path.isfile(path):
                self.warning_dialog(
                    'Invalid template name "{}". {} does not exist'.format(name, path)
                )
                return

        return path, user_path

    def _add_find_node(self, node, run, analysis_type):
        newnode = FindReferencesNode(dvc=self.dvc, analysis_type=analysis_type)
        if newnode.configure():
            node = self._get_last_node(node)

            self.pipeline.add_after(node, newnode)
            self.add_references(newnode)

            if run:
                self.run_needed = newnode

    def _add_node(self, node, new):
        node = self._get_last_node(node)
        self.pipeline.add_after(node, new)

    def _get_last_node(self, node=None):
        if node is None:
            if self.pipeline.nodes:
                idx = len(self.pipeline.nodes) - 1

                node = self.pipeline.nodes[idx]
        return node

    def _handle_figure_event(self, evt):
        kind = evt[0]
        print("fiafsfdasfsa", evt, kind)
        if kind == "alternate_figure":
            self._make_alternate_figure(evt)
        elif kind == "tag":
            self.tag_event = evt[1]
        elif kind == "identify_peaks":
            self._identify_peaks(evt[1])
        elif kind == "plot_on_map":
            self._plot_on_map()

    def _identify_peaks(self, ps):
        from pychron.pipeline.identify_peak_view import IdentifyPeakView

        source = self.application.get_service("pychron.sparrow.sparrow.Sparrow")
        if source is None:
            self.warning_dialog(
                "At least one datasource plugin is required, e.g. Sparrow"
            )
            return

        if source.connect():
            ipv = IdentifyPeakView(ps, source=source)
            open_view(ipv)
        else:
            self.warning_dialog("Failed to connect to a relevant datasource")

    def _plot_on_map(self):
        self.information_dialog("Psyche.  Plot on Map not yet implemented")

    def _make_alternate_figure(self, evt):
        self.add_pipeline = True
        _, name, groups = evt
        self._set_template(name)

        self.pipeline.nodes[0].unknowns = [ai for gi in groups for ai in gi.analyses]
        do_later(self.trait_set, run_needed=True)

    # handlers
    @on_trait_change("active_editor")
    def _handle_active_editor(self, obj, name, old, new):
        def refresh():
            self.refresh_table_needed = True

        if old:
            if hasattr(old, "figure_model"):
                old.on_trait_change(
                    refresh,
                    "figure_model:panels:figures:refresh_unknowns_table",
                    remove=True,
                )
                old.on_trait_change(
                    self._handle_figure_event,
                    "figure_model:panels:figure_event",
                    remove=True,
                )

        if new:
            if hasattr(new, "figure_model"):
                new.on_trait_change(
                    refresh, "figure_model:panels:figures:refresh_unknowns_table"
                )
                new.on_trait_change(
                    self._handle_figure_event, "figure_model:panels:figure_event"
                )

    def _add_pipeline_fired(self):
        p = self.pipeline_group.add()
        self.pipeline = p
        self.trait_setq(selected_pipeline_template="")

    def _dclicked_unknowns_changed(self):
        if self.selected_unknowns:
            self.recall_unknowns()

    def _dclicked_references_fired(self):
        if self.selected_references:
            self.recall_references()

    def _dclicked_pipeline_template_fired(self, new):
        if not isinstance(new, PipelineTemplateGroup):
            self.run_needed = True

    def _selected_pipeline_template_changed(self, new):
        if isinstance(new, (PipelineTemplate, str, tuple)):
            if self.run_enabled and not self.pipeline.active:
                self.debug("Pipeline template {} selected".format(new))
                self._set_template(new)

    _len_unknowns_cnt = 0
    _len_unknowns_removed = 0
    _len_references_cnt = 0
    _len_references_removed = 0

    def _handle_len(self, k, func):
        lr = "_len_{}_removed".format(k)
        lc = "_len_{}_cnt".format(k)

        editor = None
        if hasattr(self.selected, "editor"):
            editor = self.selected.editor

        if editor:
            n = len(getattr(self, "selected_{}".format(k)))
            if not n:
                setattr(self, lc, getattr(self, lc) + 1)

            else:
                setattr(self, lc, 0)
                setattr(self, lr, n)

        if getattr(self, lc) >= getattr(self, lr) or n == 1:
            setattr(self, lc, 0)
            if editor:
                func(editor)
                editor.refresh_needed = True

    def _dclicked_changed(self, new):
        self.configure(new)

    def _pipeline_default(self):
        return self.pipeline_group.pipelines[0]


# ============= EOF =============================================
