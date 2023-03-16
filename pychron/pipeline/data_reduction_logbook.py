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
from operator import attrgetter

from traitsui.handler import Handler
from traitsui.tabular_adapter import TabularAdapter
from traitsui.api import View, UItem, TabularEditor, HGroup, VGroup, Item
from traits.api import List, Instance, HasTraits, Any, Long, Str, Enum, Date, Property
from traitsui.menu import Action, ToolBar

from pychron.core.helpers.iterfuncs import groupby_key
from pychron.core.helpers.traitsui_shortcuts import okcancel_view
from pychron.core.pychron_traits import BorderVGroup
from pychron.dvc.dvc import DVC
from pychron.dvc.dvc_helper import get_dvc
from pychron.envisage.browser.adapters import ProjectAdapter
from pychron.envisage.browser.record_views import ProjectRecordView, SampleRecordView
from pychron.envisage.resources import icon
from pychron.loggable import Loggable
from pychron.paths import paths


class LoadAdapter(TabularAdapter):
    columns = [
        ("Name", "name"),
        ("Status", "status"),
        ("Completion Date", "completion_date"),
        ("Comment", "comment"),
    ]

    completion_date_text = Property

    def _get_bg_color(self):
        c = "lightsalmon"
        if self.item.status == "complete":
            c = "lightgreen"
        return c

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
    ]


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

    def __init__(self, record=None, *args, **kw):
        super().__init__(*args, **kw)
        if record:
            self.name = record.name

    def set_history(self, obj):
        self.comment = obj.get("comment", "")
        self.status = obj.get("status", "notstarted")
        d = obj.get("completion_date")
        if d:
            self.completion_date = datetime.datetime.strptime(d, "%Y-%m-%dT%H:%M:%S.%f")

    def tohistory(self):
        hist = {k: getattr(self, k) for k in ("comment", "status", "name")}
        hist["projects"] = [p.tohistory() for p in self.projects]
        if self.completion_date:
            hist["completion_date"] = self.completion_date.isoformat()
        return hist

    def _status_changed(self, new):
        if new == "complete":
            self.completion_date = datetime.datetime.now()


class DataReductionLogbookHandler(Handler):
    def closed(self, info, is_ok):
        info.ui.context["object"].closed()


class DataReductionLogbook(Loggable):
    loads = List
    dvc = Instance(DVC)
    selected = Instance(DataReductionLoad, ())
    selected_project = Instance(ProjectDetail, ())

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

    def _selected_changed(self):
        # get all projects for this load
        objs = self.dvc.get_data_reduction_loads()
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
                    if p.name
                    not in [
                        "REFERENCES",
                    ]
                ]

                ps = [next(pis) for g, pis in groupby_key(ps, key=lambda x: x.name)]

        self.selected.projects = [ProjectDetail(p) for p in ps]

    def traits_view(self):
        v = okcancel_view(
            UItem(
                "loads",
                editor=TabularEditor(
                    selected="selected", auto_update=True, adapter=LoadAdapter()
                ),
            ),
            HGroup(
                VGroup(
                    BorderVGroup(UItem("object.selected.status"), label="Status"),
                    BorderVGroup(
                        UItem("object.selected.comment", style="custom"),
                        label="Comment",
                    ),
                ),
                UItem(
                    "object.selected.projects",
                    editor=TabularEditor(
                        selected="selected_project", adapter=ProjectAdapter()
                    ),
                ),
            ),
            # UItem('object.selected_project.samples',
            #       editor=TabularEditor(adapter=SampleAdapter()))),
            width=800,
            toolbar=ToolBar(
                Action(name="Save", image=icon("database_save"), action="save"),
                Action(name="Share", image=icon("share"), action="share"),
            ),
            title="Data Reduction Log",
            handler=DataReductionLogbookHandler(),
        )
        return v


if __name__ == "__main__":
    paths.build("~/PychronDev")
    dr = DataReductionLogbook(dvc=get_dvc())
    dr.populate()
    dr.configure_traits()
# ============= EOF =============================================
