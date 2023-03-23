# ===============================================================================
# Copyright 2023 ross
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
import datetime
import time
from operator import attrgetter

from traitsui.handler import Handler
from traitsui.tabular_adapter import TabularAdapter
from traitsui.api import View, UItem, TabularEditor, HGroup, VGroup, Item, HSplit
from traits.api import (
    List,
    Instance,
    HasTraits,
    Any,
    Long,
    Str,
    Enum,
    Date,
    Property,
    Event,
)
from traitsui.menu import Action, ToolBar

from pychron.column_sorter_mixin import ColumnSorterMixin
from pychron.core.fuzzyfinder import fuzzyfinder
from pychron.core.helpers.iterfuncs import groupby_key
from pychron.core.helpers.traitsui_shortcuts import okcancel_view
from pychron.core.pychron_traits import BorderVGroup
from pychron.dvc.dvc import DVC
from pychron.dvc.dvc_helper import get_dvc
from pychron.envisage.browser.adapters import ProjectAdapter
from pychron.envisage.browser.record_views import (
    ProjectRecordView,
    SampleRecordView,
    LabnumberRecordView,
)
from pychron.envisage.resources import icon
from pychron.loggable import Loggable
from pychron.paths import paths
from pychron.processing.analyses.view.dvc_commit_view import DVCCommitView, HistoryView


class LoadAdapter(TabularAdapter):
    columns = [
        ("Name", "name"),
        ("Status", "status"),
        ("Run Date", "run_date"),
        ("Completion Date", "completion_date"),
        ("Comment", "comment"),
    ]

    completion_date_text = Property
    run_date_text = Property

    def _get_bg_color(self):
        c = "lightsalmon"
        if self.item.status == "complete":
            c = "lightgreen"
        return c

    def _get_run_date_text(self):
        d = self.item.run_date
        if d:
            d = d.date().isoformat()

        return d

    def _get_completion_date_text(self):
        d = self.item.completion_date
        if d:
            d = d.date().isoformat()

        return d


class ProjectAdapter(TabularAdapter):
    columns = [
        ("Project Name", "name"),
    ]


class SampleAdapter(TabularAdapter):
    columns = [
        ("Sample Name", "name"),
        ("Identifier", "identifier"),
        ("Analysis Count", "analysis_count"),
        ("Reduction", "reduction_state"),
    ]

    def _get_bg_color(self):
        color = "grey"
        if self.item.reduction_state is not None:
            if self.item.reduction_state == "complete":
                color = "lightgreen"
            elif self.item.reduction_state == "partial":
                color = "yellow"
            else:
                color = "lightsalmon"

        return color


class ProjectDetail(HasTraits):
    name = Str
    samples = List

    def __init__(self, record=None, *args, **kw):
        super().__init__(*args, **kw)
        if record:
            if hasattr(record, "name"):
                self.name = record.name
            else:
                self.name = record.get("name")

    def tohistory(self):
        return {"name": self.name}


# class LoadDetail(HasTraits):
#     projects = List
#     samples = List
#     selected_project = Any
#
#     # def populate(self, selected):
#     #     # get all projects for this load
#     #     objs = self.dvc.get_data_reduction_loads()
#     #     for oi in objs:
#     #         if oi['name'] == selected.name:
#     #             if 'projects' in oi:
#     #                 ps = oi['projects']
#     #                 print('founasd', ps)
#     #                 break
#     #     else:
#     #         print('uaisnasdf')
#     #         with self.dvc.session_ctx() as sess:
#     #             load = self.dvc.get_load(selected.name)
#     #
#     #             ps = [p.analysis.irradiation_position.sample.project
#     #                   for p in load.measured_positions]
#     #             ps = [p for p in ps if p.name not in ['REFERENCES', ]]
#     #
#     #             ps = [next(pis) for g, pis in groupby_key(ps, key=lambda x: x.name)]
#     #
#     #     self.projects = [ProjectDetail(p) for p in ps]
#     #         # self.projects = [ProjectRecordView(next(pis)) for g, pis in ps]
#
#     def _selected_project_changed(self):
#         with self.dvc.session_ctx() as sess:
#             proj = self.dvc.get_project_by_id(self.selected_project.unique_id)
#             self.samples = [SampleRecordView(s) for s in proj.samples]
#
#     def traits_view(self):
#         v = View(HGroup(UItem('projects', editor=TabularEditor(selected='selected_project',
#                                                                adapter=ProjectAdapter())),
#                         UItem('samples', editor=TabularEditor(adapter=SampleAdapter()))))
#         return v


class DataReductionLoad(HasTraits):
    name = Str
    status = Enum("notstarted", "complete", "incomplete")
    comment = Str
    completion_date = Date
    projects = List
    samples = List
    run_date = Date

    def __init__(self, record=None, *args, **kw):
        super().__init__(*args, **kw)
        if record:
            self.name = record.name
            self.run_date = record.create_date

    def set_history(self, obj):
        self.comment = obj.get("comment", "")
        self.status = obj.get("status", "notstarted")
        d = obj.get("completion_date")
        if d:
            self.completion_date = datetime.datetime.strptime(d, "%Y-%m-%dT%H:%M:%S.%f")

        d = obj.get("run_date")
        if d:
            self.run_date = datetime.datetime.strptime(d, "%Y-%m-%dT%H:%M:%S")
            # try:
            #     self.run_date = datetime.datetime.strptime(d, '%Y-%m-%dT%H:%M:%S.%f')
            # except ValueError:

    def tohistory(self):
        hist = {k: getattr(self, k) for k in ("comment", "status", "name")}
        hist["projects"] = [p.tohistory() for p in self.projects]
        if self.completion_date:
            hist["completion_date"] = self.completion_date.isoformat()

        if self.run_date:
            hist["run_date"] = self.run_date.isoformat()

        return hist

    def _status_changed(self, new):
        if new == "complete":
            self.completion_date = datetime.datetime.now()


class DataReductionLogbookHandler(Handler):
    def closed(self, info, is_ok):
        info.ui.context["object"].closed()


class DataReductionLogbook(Loggable, ColumnSorterMixin):
    loads = List
    oloads = List

    dvc = Instance(DVC)
    selected = Instance(DataReductionLoad, ())
    selected_project = Instance(ProjectDetail, ())
    selected_sample = Instance(SampleRecordView)
    search_entry = Str  # (auto_set=False, enter_set=True)
    sample_column_clicked = Event

    update = Event

    _cached_loads = None

    def examine(self):
        self.debug("examine")
        if self.selected:
            # get all the analyses for this load
            with self.dvc.session_ctx():
                l = self.dvc.get_load(self.selected.name)
                anss = []
                for m in l.measured_positions:
                    if self.selected_project:
                        if (
                                self.selected_project.name
                                != m.analysis.irradiation_position.sample.project.name
                        ):
                            continue

                    if self.selected_sample:
                        if (
                                self.selected_sample.name
                                != m.analysis.irradiation_position.sample.name
                        ):
                            # print('skippoing', m.analysis.irradiation_position.sample.name)
                            continue

                    anss.append(m.analysis)

                anns = self.dvc.make_analyses(anss)

                for rname, gs in groupby_key(
                        anns, key=lambda x: x.repository_identifier
                ):
                    repo = self.dvc.get_repository(rname)
                    for sa, ais in groupby_key(list(gs), key=lambda x: x.identifier):
                        reduction_state = "no reduction"
                        states = []
                        for ai in ais:
                            dcv = HistoryView()
                            dcv.initialize(ai, repo=repo._repo)

                            state = len(dcv.commits) > 4
                            states.append(state)
                            if state:
                                ai.is_reduced = True

                        if all(states):
                            reduction_state = "complete"
                        elif any(states):
                            reduction_state = "partial"

                        ss = next(
                            (s for s in self.selected.samples if s.identifier == sa)
                        )
                        ss.reduction_state = reduction_state
                self.update = True

    def populate(self):
        loads = self.dvc.get_data_reduction_loads()
        ls = []
        for li in self.dvc.get_loads():
            la = DataReductionLoad(li)
            for lj in loads:
                if lj["name"] == la.name:
                    la.set_history(lj)
                    break
            ls.append(la)

        self.loads = ls
        self.oloads = ls

    def save(self, *args, **kw):
        self.debug("save")
        objs = [l.tohistory() for l in self.loads]
        self.dvc.save_data_reduction_loads(objs)

    def share(self):
        self.save()
        self.dvc.share_data_reduction_loads()
        self.information_dialog("Data Reduction Log shared")

    def closed(self):
        if self.confirmation_dialog("Would you like to share your changes?"):
            self.share()

    def _sample_column_clicked_fired(self, new):
        self._column_clicked_handled(new)

    def _search_entry_changed(self, new):
        if new:
            # for o in self.oloads:
            #     print(o.name.lower(),o.name.lower().startswith(new), new)
            # self.loads = [l for l in self.oloads if l.name.lower().startswith(new.lower())]
            self.loads = fuzzyfinder(new, self.oloads, "name")

    def _selected_changed(self):
        # get all projects for this load
        objs = self.dvc.get_data_reduction_loads()

        save = False
        for oi in objs:
            if oi["name"] == self.selected.name:
                if "projects" in oi:
                    ps = oi["projects"]
                    if ps:
                        break
        else:
            with self.dvc.session_ctx() as sess:
                load = self.dvc.get_load(self.selected.name)

                ps = [
                    p.analysis.irradiation_position.sample.project
                    for p in load.measured_positions
                ]
                ps = [
                    p
                    for p in ps
                    if p.name not in [
                           "REFERENCES",
                       ]
                ]

                ps = [next(pis) for g, pis in groupby_key(ps, key=lambda x: x.name)]
                save = True

        self.selected.projects = [ProjectDetail(p) for p in ps]
        if save:
            self.save()
            self.dvc.clear_data_reduction_loads_cache()

    def _selected_project_changed(self, new):
        with self.dvc.session_ctx() as sess:
            ls = []
            for li in self.dvc.get_labnumbers(projects=[new.name], loads=[self.selected.name]):
                if li.analyzed:
                    r = LabnumberRecordView(li)
                    ls.append(r)

            self.selected.samples = ls

    def traits_view(self):
        v = View(
            UItem("search_entry"),
            UItem(
                "loads",
                editor=TabularEditor(
                    column_clicked="column_clicked",
                    selected="selected",
                    editable=False,
                    auto_update=True,
                    adapter=LoadAdapter(),
                ),
            ),
            HSplit(
                VGroup(
                    BorderVGroup(UItem("object.selected.status"), label="Status"),
                    BorderVGroup(
                        UItem("object.selected.comment", style="custom"),
                        label="Comment",
                    ),
                ),
                HGroup(
                    UItem(
                        "object.selected.projects",
                        width=300,
                        editor=TabularEditor(
                            selected="selected_project",
                            editable=False,
                            adapter=ProjectAdapter(),
                        ),
                    ),
                    UItem(
                        "object.selected.samples",
                        width=300,
                        editor=TabularEditor(
                            adapter=SampleAdapter(),
                            editable=False,
                            update="update",
                            selected="object.selected_sample",
                            column_clicked="sample_column_clicked",
                            stretch_last_section=False,
                        ),
                    ),
                ),
            ),
            # UItem('object.selected_project.samples',
            #       editor=TabularEditor(adapter=SampleAdapter()))),
            width=900,
            toolbar=ToolBar(
                Action(name="Save", image=icon("database_save"), action="save"),
                Action(name="Share", image=icon("share"), action="share"),
                Action(
                    name="History",
                    image=icon("history"),
                    action="examine",
                    enabled_when="object.selected",
                ),
            ),
            title="Data Reduction Log",
            handler=DataReductionLogbookHandler(),
            resizable=True,
        )
        return v


if __name__ == "__main__":
    paths.build("~/PychronDev")
    dr = DataReductionLogbook(dvc=get_dvc())
    dr.populate()
    dr.configure_traits()
# ============= EOF =============================================
