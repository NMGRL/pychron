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
import six
from pyface.action.menu_manager import MenuManager
from pyface.tasks.traits_dock_pane import TraitsDockPane
from traits.api import Int, Property, Button, Instance
from traits.has_traits import MetaHasTraits
from traitsui.api import (
    View,
    UItem,
    VGroup,
    InstanceEditor,
    HGroup,
    VSplit,
    Handler,
    TabularEditor,
    TreeEditor,
)
from traitsui.menu import Action
from traitsui.tabular_adapter import TabularAdapter
from traitsui.tree_node import TreeNode
from uncertainties import nominal_value, std_dev

from pychron.core.configurable_tabular_adapter import ConfigurableMixin
from pychron.core.helpers.color_generators import colornames
from pychron.core.helpers.formatting import floatfmt
from pychron.core.ui.enum_editor import myEnumEditor
from pychron.core.ui.qt.tree_editor import PipelineEditor
from pychron.core.ui.table_configurer import TableConfigurer
from pychron.core.ui.tabular_editor import myTabularEditor
from pychron.envisage.browser.view import PaneBrowserView
from pychron.envisage.icon_button_editor import icon_button_editor
from pychron.pipeline.engine import Pipeline, PipelineGroup, NodeGroup
from pychron.pipeline.nodes import FindReferencesNode
from pychron.pipeline.nodes.base import BaseNode
from pychron.pipeline.nodes.data import DataNode, InterpretedAgeNode
from pychron.pipeline.nodes.figure import IdeogramNode, SpectrumNode, SeriesNode
from pychron.pipeline.nodes.filter import FilterNode, MSWDFilterNode
from pychron.pipeline.nodes.find import FindFluxMonitorsNode
from pychron.pipeline.nodes.fit import (
    FitIsotopeEvolutionNode,
    FitBlanksNode,
    FitICFactorNode,
    FitFluxNode,
)
from pychron.pipeline.nodes.grouping import GroupingNode, SubGroupingNode
from pychron.pipeline.nodes.persist import PDFNode, DVCPersistNode
from pychron.pipeline.nodes.review import ReviewNode
from pychron.pipeline.tasks.tree_node import (
    SeriesTreeNode,
    PDFTreeNode,
    GroupingTreeNode,
    SpectrumTreeNode,
    IdeogramTreeNode,
    FilterTreeNode,
    DataTreeNode,
    DBSaveTreeNode,
    FindTreeNode,
    FitTreeNode,
    PipelineTreeNode,
    ReviewTreeNode,
    PipelineGroupTreeNode,
    NodeGroupTreeNode,
)
from pychron.pipeline.template import (
    PipelineTemplate,
    PipelineTemplateGroup,
    PipelineTemplateRoot,
)
from pychron.pychron_constants import PLUSMINUS_ONE_SIGMA, LIGHT_RED, LIGHT_YELLOW


class TemplateTreeNode(TreeNode):
    def get_icon(self, obj, is_expanded):
        icon = obj.icon

        if not icon:
            icon = super(TemplateTreeNode, self).get_icon(obj, is_expanded)
        return icon


def node_adder(name):
    def wrapper(obj, info, o):
        # print name, info.object
        f = getattr(info.object, name)
        f(o)

    return wrapper


class PipelineHandlerMeta(MetaHasTraits):
    def __new__(cls, *args, **kwargs):
        klass = MetaHasTraits.__new__(cls, *args, **kwargs)
        for t in (
            "review",
            "pdf_figure",
            "iso_evo_persist",
            "data",
            "filter",
            "mswd_filter",
            "ideogram",
            "spectrum",
            "series",
            "isotope_evolution",
            "blanks",
            "detector_ic",
            "flux",
            "find_blanks",
            "find_airs",
            "icfactor",
            "push",
            "audit",
            "inverse_isochron",
            "grouping",
            "graph_grouping",
            "subgrouping",
            "set_interpreted_age",
            "interpreted_ages",
        ):
            name = "add_{}".format(t)
            setattr(klass, name, node_adder(name))

        for c in ("isotope_evolution", "blanks", "ideogram", "spectrum", "icfactors"):
            name = "chain_{}".format(c)
            setattr(klass, name, node_adder(name))

        return klass


class PipelineHandler(six.with_metaclass(PipelineHandlerMeta, Handler)):
    def save_template(self, info, obj):
        info.object.save_pipeline_template()

    def review_node(self, info, obj):
        info.object.review_node(obj)

    def delete_node(self, info, obj):
        info.object.remove_node(obj)

    def enable(self, info, obj):
        self._toggle_enable(info, obj, True)

    def disable(self, info, obj):
        self._toggle_enable(info, obj, False)

    def enable_permanent(self, info, obj):
        self._toggle_permanent(info, obj, True)

    def disable_permanent(self, info, obj):
        self._toggle_permanent(info, obj, False)

    def toggle_skip_configure(self, info, obj):
        obj.skip_configure = not obj.skip_configure
        info.object.update_needed = True

    def configure(self, info, obj):
        info.object.configure(obj)

    def move_up(self, info, obj):
        info.object.pipeline.move_up(obj)
        info.object.selected = obj

    def move_down(self, info, obj):
        info.object.pipeline.move_down(obj)
        info.object.selected = obj

    def _toggle_permanent(self, info, obj, state):
        info.object.set_review_permanent(state)
        self._toggle_enable(info, obj, state)

    def _toggle_enable(self, info, obj, state):
        obj.enabled = state
        info.object.refresh_all_needed = True
        info.object.update_needed = True


class PipelinePane(TraitsDockPane):
    name = "Pipeline"
    id = "pychron.pipeline.pane"

    def traits_view(self):
        def enable_disable_menu_factory():
            return MenuManager(
                Action(
                    name="Enable", action="enable", visible_when="not object.enabled"
                ),
                Action(name="Disable", action="disable", visible_when="object.enabled"),
                Action(
                    name="Enable Permanent",
                    action="enable_permanent",
                    visible_when="not object.enabled",
                ),
                Action(
                    name="Disable Permanent",
                    action="disable_permanent",
                    visible_when="object.enabled",
                ),
                name="Enable/Disable",
            )

        def menu_factory(*actions):
            return MenuManager(
                Action(name="Configure", action="configure"),
                Action(
                    name="Enable Auto Configure",
                    action="toggle_skip_configure",
                    visible_when="object.skip_configure",
                ),
                Action(
                    name="Disable Auto Configure",
                    action="toggle_skip_configure",
                    visible_when="not object.skip_configure",
                ),
                Action(name="Move Up", action="move_up"),
                Action(name="Move Down", action="move_down"),
                Action(name="Delete", action="delete_node"),
                Action(name="Save Template", action="save_template"),
                *actions
            )

        def add_menu_factory():
            fig_menu = MenuManager(
                Action(name="Add Inverse Isochron", action="add_inverse_isochron"),
                Action(name="Add Ideogram", action="add_ideogram"),
                Action(name="Add Spectrum", action="add_spectrum"),
                Action(name="Add Series", action="add_series"),
                name="Figure",
            )
            grp_menu = MenuManager(
                Action(name="Add Grouping", action="add_grouping"),
                Action(name="Add Graph Grouping", action="add_graph_grouping"),
                Action(name="Add SubGrouping", action="add_subgrouping"),
                name="Grouping",
            )
            filter_menu = MenuManager(
                Action(name="Add Filter", action="add_filter"),
                Action(name="Add MSWD Filter", action="add_mswd_filter"),
                name="Filter",
            )

            return MenuManager(
                Action(name="Add Unknowns", action="add_data"),
                Action(name="Add Interpreted Ages", action="add_interpreted_ages"),
                grp_menu,
                filter_menu,
                fig_menu,
                Action(name="Add Set IA", action="add_set_interpreted_age"),
                Action(name="Add Review", action="add_review"),
                Action(name="Add Audit", action="add_audit"),
                Action(name="Add Push"),
                name="Add",
            )

        def fit_menu_factory():
            return MenuManager(
                Action(name="Isotope Evolution", action="add_isotope_evolution"),
                Action(name="Blanks", action="add_blanks"),
                Action(name="IC Factor", action="add_icfactor"),
                Action(name="Detector IC", enabled=False, action="add_detector_ic"),
                Action(name="Flux", enabled=False, action="add_flux"),
                name="Fit",
            )

        def save_menu_factory():
            return MenuManager(
                Action(name="Save PDF Figure", action="add_pdf_figure"),
                Action(name="Save Iso Evo", action="add_iso_evo_persist"),
                Action(name="Save Blanks", action="add_blanks_persist"),
                Action(name="Save ICFactor", action="add_icfactor_persist"),
                name="Save",
            )

        def find_menu_factory():
            return MenuManager(
                Action(name="Blanks", action="add_find_blanks"),
                Action(name="Airs", action="add_find_airs"),
                name="Find",
            )

        def chain_menu_factory():
            return MenuManager(
                Action(name="Chain Ideogram", action="chain_ideogram"),
                Action(
                    name="Chain Isotope Evolution", action="chain_isotope_evolution"
                ),
                Action(name="Chain Spectrum", action="chain_spectrum"),
                Action(name="Chain Blanks", action="chain_blanks"),
                Action(name="Chain ICFactors", action="chain_icfactors"),
                name="Chain",
            )

        # ------------------------------------------------

        def data_menu_factory():
            return menu_factory(
                enable_disable_menu_factory(),
                add_menu_factory(),
                fit_menu_factory(),
                chain_menu_factory(),
                find_menu_factory(),
            )

        def filter_menu_factory():
            return menu_factory(
                enable_disable_menu_factory(),
                add_menu_factory(),
                fit_menu_factory(),
                chain_menu_factory(),
            )

        def figure_menu_factory():
            return menu_factory(
                enable_disable_menu_factory(),
                add_menu_factory(),
                fit_menu_factory(),
                chain_menu_factory(),
                save_menu_factory(),
            )

        def ffind_menu_factory():
            return menu_factory(
                Action(name="Review", action="review_node"),
                enable_disable_menu_factory(),
                add_menu_factory(),
                fit_menu_factory(),
            )

        nodes = [
            PipelineGroupTreeNode(
                node_for=[PipelineGroup], children="pipelines", auto_open=True
            ),
            PipelineTreeNode(
                node_for=[Pipeline],
                children="nodes",
                icon_open="",
                label="name",
                auto_open=True,
            ),
            NodeGroupTreeNode(
                node_for=[NodeGroup], children="nodes", auto_open=True, label="name"
            ),
            DataTreeNode(
                node_for=[DataNode, InterpretedAgeNode], menu=data_menu_factory()
            ),
            FilterTreeNode(
                node_for=[FilterNode, MSWDFilterNode], menu=filter_menu_factory()
            ),
            IdeogramTreeNode(node_for=[IdeogramNode], menu=figure_menu_factory()),
            SpectrumTreeNode(node_for=[SpectrumNode], menu=figure_menu_factory()),
            SeriesTreeNode(node_for=[SeriesNode], menu=figure_menu_factory()),
            PDFTreeNode(node_for=[PDFNode], menu=menu_factory()),
            GroupingTreeNode(
                node_for=[GroupingNode, SubGroupingNode], menu=data_menu_factory()
            ),
            DBSaveTreeNode(node_for=[DVCPersistNode], menu=data_menu_factory()),
            FindTreeNode(
                node_for=[FindReferencesNode, FindFluxMonitorsNode],
                menu=ffind_menu_factory(),
            ),
            FitTreeNode(
                node_for=[
                    FitIsotopeEvolutionNode,
                    FitICFactorNode,
                    FitBlanksNode,
                    FitFluxNode,
                ],
                menu=ffind_menu_factory(),
            ),
            ReviewTreeNode(node_for=[ReviewNode], menu=enable_disable_menu_factory()),
            PipelineTreeNode(node_for=[BaseNode], label="name"),
        ]

        editor = PipelineEditor(
            nodes=nodes,
            editable=False,
            selected="selected",
            dclick="dclicked",
            hide_root=True,
            lines_mode="off",
            show_disabled=True,
            refresh_all_icons="refresh_all_needed",
            update="update_needed",
        )

        tnodes = [
            TreeNode(node_for=[PipelineTemplateRoot], children="groups"),
            TemplateTreeNode(
                node_for=[PipelineTemplateGroup], label="name", children="templates"
            ),
            TemplateTreeNode(
                node_for=[
                    PipelineTemplate,
                ],
                label="name",
            ),
        ]

        teditor = TreeEditor(
            nodes=tnodes,
            editable=False,
            selected="selected_pipeline_template",
            dclick="dclicked_pipeline_template",
            hide_root=True,
            lines_mode="off",
        )

        v = View(
            VSplit(
                UItem("pipeline_template_root", editor=teditor),
                VGroup(
                    HGroup(
                        icon_button_editor(
                            "run_needed", "start", visible_when="run_enabled"
                        ),
                        icon_button_editor(
                            "run_needed", "edit-redo-3", visible_when="resume_enabled"
                        ),
                        icon_button_editor("add_pipeline", "add"),
                    ),
                    UItem("pipeline_group", editor=editor),
                ),
            ),
            handler=PipelineHandler(),
        )
        return v


class BaseAnalysesAdapter(TabularAdapter, ConfigurableMixin):
    font = "arial 10"
    rundate_text = Property
    record_id_width = Int(80)
    tag_width = Int(50)
    sample_width = Int(80)

    def _get_rundate_text(self):
        try:
            r = self.item.rundate.strftime("%m-%d-%Y %H:%M")
        except AttributeError:
            r = ""
        return r

    def get_bg_color(self, obj, trait, row, column=0):
        if self.item.tag == "invalid":
            c = "#C9C5C5"
        elif self.item.is_omitted():
            c = "#FAC0C0"
        else:
            c = super(BaseAnalysesAdapter, self).get_bg_color(obj, trait, row, column)
        return c


class UnknownsAdapter(BaseAnalysesAdapter):
    columns = [
        ("Run ID", "record_id"),
        ("Sample", "sample"),
        ("Age", "age"),
        ("Comment", "comment"),
        ("Tag", "tag"),
        ("GroupID", "group_id"),
    ]

    all_columns = [
        ("RunDate", "rundate"),
        ("Run ID", "record_id"),
        ("Aliquot", "aliquot"),
        ("Step", "step"),
        ("UUID", "display_uuid"),
        ("Sample", "sample"),
        ("Project", "project"),
        ("RepositoryID", "repository_identifier"),
        ("Age", "age"),
        ("Age {}".format(PLUSMINUS_ONE_SIGMA), "age_error"),
        ("F", "f"),
        ("F {}".format(PLUSMINUS_ONE_SIGMA), "f_error"),
        ("Saved J", "j"),
        ("Saved J {}".format(PLUSMINUS_ONE_SIGMA), "j_error"),
        ("Model J", "model_j"),
        ("Model J {}".format(PLUSMINUS_ONE_SIGMA), "model_j_error"),
        ("Model J Kind", "model_j_kind"),
        ("Comment", "comment"),
        ("Tag", "tag"),
        ("GroupID", "group_id"),
        ("GraphID", "graph_id"),
    ]
    age_width = Int(70)
    error_width = Int(60)
    graph_id_width = Int(30)

    age_text = Property
    age_error_text = Property
    j_error_text = Property
    j_text = Property
    f_error_text = Property
    f_text = Property

    model_j_error_text = Property
    model_j_text = Property

    def __init__(self, *args, **kw):
        super(UnknownsAdapter, self).__init__(*args, **kw)
        # self._ncolors = len(colornames)

        self.set_colors(colornames)

    def set_colors(self, colors):
        self._colors = colors
        self._ncolors = len(colors)

    def get_menu(self, obj, trait, row, column):
        grp = MenuManager(
            Action(name="Group Selected", action="unknowns_group_by_selected"),
            Action(name="Aux Group Selected", action="unknowns_aux_group_by_selected"),
            Action(name="Group by Sample", action="unknowns_group_by_sample"),
            Action(name="Group by Aliquot", action="unknowns_group_by_aliquot"),
            Action(name="Group by Identifier", action="unknowns_group_by_identifier"),
            Action(name="Clear Group", action="unknowns_clear_grouping"),
            Action(name="Clear All Group", action="unknowns_clear_all_grouping"),
            name="Plot Grouping",
        )

        return MenuManager(
            Action(name="Recall", action="recall_unknowns"),
            Action(
                name="Graph Group Selected", action="unknowns_graph_group_by_selected"
            ),
            Action(name="Save Analysis Group", action="save_analysis_group"),
            Action(name="Toggle Status", action="unknowns_toggle_status"),
            Action(name="Configure", action="configure_unknowns"),
            Action(name="Play Video...", action="play_analysis_video"),
            grp,
        )

    def _get_f_text(self):
        r = floatfmt(self.item.f, n=4)
        return r

    def _get_f_error_text(self):
        r = floatfmt(self.item.f_err, n=4)
        return r

    def _get_j_text(self):
        r = floatfmt(nominal_value(self.item.j), n=8)
        return r

    def _get_j_error_text(self):
        r = floatfmt(std_dev(self.item.j), n=8)
        return r

    def _get_model_j_text(self):
        r = ""
        if self.item.modeled_j:
            r = floatfmt(nominal_value(self.item.modeled_j), n=8)
        return r

    def _get_model_j_error_text(self):
        r = ""
        if self.item.modeled_j:
            r = floatfmt(std_dev(self.item.modeled_j), n=8)
        return r

    def _get_age_text(self):
        r = floatfmt(nominal_value(self.item.uage), n=3)
        return r

    def _get_age_error_text(self):
        r = floatfmt(std_dev(self.item.uage), n=4)
        return r

    def get_text_color(self, obj, trait, row, column=0):
        color = "black"
        item = getattr(obj, trait)[row]
        gid = item.group_id or item.aux_id
        cid = gid % self._ncolors if self._ncolors else 0

        try:
            color = self._colors[cid]
        except IndexError:
            pass
        return color


class ReferencesAdapter(BaseAnalysesAdapter):
    columns = [("Run ID", "record_id"), ("Comment", "comment")]

    all_columns = [
        ("RunDate", "rundate"),
        ("Run ID", "record_id"),
        ("Aliquot", "aliquot"),
        ("UUID", "display_uuid"),
        ("Sample", "sample"),
        ("Project", "project"),
        ("RepositoryID", "repository_identifier"),
        ("Comment", "comment"),
        ("Tag", "tag"),
    ]

    def get_menu(self, object, trait, row, column):
        return MenuManager(
            Action(name="Recall", action="recall_references"),
            Action(name="Configure", action="configure_references"),
        )


class AnalysesPaneHandler(Handler):
    def unknowns_group_by_sample(self, info, obj):
        obj = info.ui.context["object"]
        obj.unknowns_group_by("sample")

    def unknowns_group_by_identifier(self, info, obj):
        obj = info.ui.context["object"]
        obj.unknowns_group_by("identifier")

    def unknowns_group_by_aliquot(self, info, obj):
        obj = info.ui.context["object"]
        obj.unknowns_group_by("aliquot")

    def unknowns_graph_group_by_selected(self, info, obj):
        obj = info.ui.context["object"]
        obj.group_selected("graph_id")

    def unknowns_group_by_selected(self, info, obj):
        obj = info.ui.context["object"]
        obj.group_selected("group_id")

    def unknowns_aux_group_by_selected(self, info, obj):
        obj = info.ui.context["object"]
        obj.group_selected("aux_id")

    def unknowns_clear_grouping(self, info, obj):
        obj = info.ui.context["object"]
        obj.unknowns_clear_grouping()

    def unknowns_clear_all_grouping(self, info, obj):
        obj = info.ui.context["object"]
        obj.unknowns_clear_all_grouping()

    def unknowns_toggle_status(self, info, obj):
        obj = info.ui.context["object"]
        obj.unknowns_toggle_status()

    def save_analysis_group(self, info, obj):
        obj = info.ui.context["object"]
        obj.save_analysis_group()

    def play_analysis_video(self, info, obj):
        obj = info.ui.context["object"]
        obj.play_analysis_video()

    def recall_unknowns(self, info, obj):
        obj = info.ui.context["object"]
        obj.recall_unknowns()

    def recall_references(self, info, obj):
        obj = info.ui.context["object"]
        obj.recall_references()

    def configure_unknowns(self, info, obj):
        pane = info.ui.context["pane"]
        pane.configure_unknowns()

    def configure_references(self, info, obj):
        pane = info.ui.context["pane"]
        pane.configure_references()


class UnknownsTableConfigurer(TableConfigurer):
    id = "unknowns_pane"


class ReferencesTableConfigurer(TableConfigurer):
    id = "references_pane"


class AnalysesPane(TraitsDockPane):
    name = "Analyses"
    id = "pychron.pipeline.analyses"

    unknowns_adapter = Instance(UnknownsAdapter)
    unknowns_table_configurer = Instance(UnknownsTableConfigurer, ())

    references_adapter = Instance(ReferencesAdapter)
    references_table_configurer = Instance(ReferencesTableConfigurer, ())

    def configure_unknowns(self):
        self.unknowns_table_configurer.edit_traits()

    def configure_references(self):
        self.references_table_configurer.edit_traits()

    def _unknowns_adapter_default(self):
        a = UnknownsAdapter()
        self.unknowns_table_configurer.set_adapter(a)
        return a

    def _references_adapter_default(self):
        a = ReferencesAdapter()
        self.references_table_configurer.set_adapter(a)
        return a

    def traits_view(self):
        v = View(
            VGroup(
                UItem(
                    "object.selected.unknowns",
                    width=200,
                    editor=TabularEditor(
                        adapter=self.unknowns_adapter,
                        update="refresh_table_needed",
                        multi_select=True,
                        column_clicked="object.selected.column_clicked",
                        # drag_external=True,
                        # drop_factory=self.model.drop_factory,
                        dclicked="dclicked_unknowns",
                        selected="selected_unknowns",
                        operations=["delete"],
                    ),
                ),
                UItem(
                    "object.selected.references",
                    visible_when="object.selected.references",
                    editor=TabularEditor(
                        adapter=self.references_adapter,
                        update="refresh_table_needed",
                        # drag_external=True,
                        multi_select=True,
                        dclicked="dclicked_references",
                        selected="selected_references",
                        operations=["delete"],
                    ),
                ),
            ),
            handler=AnalysesPaneHandler(),
        )
        return v


class RepositoryTabularAdapter(TabularAdapter):
    columns = [("Name", "name"), ("Ahead", "ahead"), ("Behind", "behind")]

    def get_menu(self, obj, trait, row, column):
        return MenuManager(
            Action(name="Refresh Status", action="refresh_repository_status"),
            Action(name="Get Changes", action="pull"),
            Action(name="Share Changes", action="push"),
            Action(name="Delete Local Changes", action="delete_local_changes"),
        )

    def get_bg_color(self, obj, trait, row, column=0):
        if self.item.behind:
            c = LIGHT_RED
        elif self.item.ahead:
            c = LIGHT_YELLOW
        else:
            c = "white"
        return c


class RepositoryPaneHandler(Handler):
    def refresh_repository_status(self, info, obj):
        obj.refresh_repository_status()

    def pull(self, info, obj):
        obj.pull()

    def push(self, info, obj):
        obj.push()

    def delete_local_changes(self, info, obj):
        obj.delete_local_changes()
        obj.refresh_repository_status()


class RepositoryPane(TraitsDockPane):
    name = "Repositories"
    id = "pychron.pipeline.repository"

    def traits_view(self):
        v = View(
            UItem(
                "object.repositories",
                editor=myTabularEditor(
                    adapter=RepositoryTabularAdapter(),
                    editable=False,
                    multi_select=True,
                    refresh="object.refresh_needed",
                    selected="object.selected_repositories",
                ),
            ),
            handler=RepositoryPaneHandler(),
        )
        return v


class EditorOptionsPane(TraitsDockPane):
    name = "Editor Options"
    id = "pychron.pipeline.editor_options"

    def traits_view(self):
        v = View(
            UItem(
                "object.active_editor_options", style="custom", editor=InstanceEditor()
            )
        )
        return v


class BrowserPane(TraitsDockPane, PaneBrowserView):
    id = "pychron.browser.pane"
    name = "Analysis Selection"


class SearcherPane(TraitsDockPane):
    name = "Search"
    id = "pychron.browser.searcher.pane"
    add_search_entry_button = Button

    def _add_search_entry_button_fired(self):
        self.model.add_search_entry()

    def traits_view(self):
        v = View(
            VGroup(
                HGroup(
                    UItem("search_entry"),
                    UItem(
                        "search_entry",
                        editor=myEnumEditor(name="search_entries"),
                        width=-35,
                    ),
                    icon_button_editor("pane.add_search_entry_button", "add"),
                ),
                UItem(
                    "object.table.analyses",
                    editor=myTabularEditor(
                        adapter=self.model.table.tabular_adapter,
                        operations=["move", "delete"],
                        column_clicked="object.table.column_clicked",
                        refresh="object.table.refresh_needed",
                        selected="object.table.selected",
                        dclicked="object.table.dclicked",
                    ),
                ),
            )
        )
        return v


# ============= EOF =============================================
