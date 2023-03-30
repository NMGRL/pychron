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
import json
import os
import time
from operator import attrgetter

from traitsui.handler import Handler
from traitsui.tabular_adapter import TabularAdapter
from traitsui.api import (
    View,
    UItem,
    TabularEditor,
    HGroup,
    VGroup,
    Item,
    HSplit,
    VSplit,
)
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
    Int,
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
from pychron.envisage.icon_button_editor import icon_button_editor
from pychron.envisage.resources import icon
from pychron.loggable import Loggable
from pychron.paths import paths
from pychron.processing.analyses.view.dvc_commit_view import DVCCommitView, HistoryView


class ColorTabularAdapter(TabularAdapter):
    def _get_bg_color(self):
        c = "lightsalmon"
        if self.item.reduction_state == "complete":
            c = "lightgreen"
        elif self.item.reduction_state == "incomplete":
            c = "yellow"

        return c


class LoadAdapter(ColorTabularAdapter):
    columns = [
        ("Name", "name"),
        ("Status", "reduction_state"),
        ("Run Date", "run_date"),
        ("Completion Date", "completion_date"),
        ("Comment", "comment"),
    ]
    name_width = Int(75)
    status_width = Int(85)
    run_date_width = Int(100)
    completion_date_text = Property
    run_date_text = Property

    def _get_bg_color(self):
        c = "lightsalmon"
        if self.item.reduction_state == "complete":
            c = "lightgreen"
        elif self.item.reduction_state == "incomplete":
            c = "yellow"
        elif not self.item.examined:
            c = "lightblue"
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


class ProjectAdapter(ColorTabularAdapter):
    columns = [("Project Name", "name"), ("UniqueID", "unique_id")]


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


class LabnumberRecordViewDRDetai(LabnumberRecordView):
    reduction_state = "no reduction"

    def tohistory(self):
        return {
            "identifier": self.identifier,
            "analysis_count": self.analysis_count,
            "reduction_state": self.reduction_state,
        }


class ProjectDetail(HasTraits):
    name = Str
    samples = List
    reduction_state = Enum("notstarted", "incomplete", "complete")
    unique_id = Long

    def __init__(self, record=None, *args, **kw):
        super().__init__(*args, **kw)
        if record:
            if hasattr(record, "name"):
                self.name = record.name
                self.unique_id = record.id
            else:
                self.name = record.get("name")
                self.unique_id = record.get("unique_id", 0)
                self.reduction_state = record.get("reduction_state", "notstarted")

    def determine_reduction_state(self):
        r = "notstarted"
        if all((s.reduction_state == "complete" for s in self.samples)):
            r = "complete"
        elif any((s.reduction_state == "complete" for s in self.samples)):
            r = "incomplete"
        return r

    def tohistory(self):
        return {
            "name": self.name,
            "unique_id": self.unique_id,
            "reduction_state": self.determine_reduction_state(),
            "samples": [si.tohistory() for si in self.samples],
        }


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
    reduction_state = Enum("notstarted", "complete", "incomplete")
    examined = False
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
        self.reduction_state = obj.get("reduction_state", "notstarted")
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
        hist = {k: getattr(self, k) for k in ("comment", "reduction_state", "name")}
        hist["projects"] = [p.tohistory() for p in self.projects]
        if self.completion_date:
            hist["completion_date"] = self.completion_date.isoformat()

        if self.run_date:
            hist["run_date"] = self.run_date.isoformat()

        return hist

    def determine_status(self):
        if self.projects:
            if all(
                (p.determine_reduction_state() == "complete" for p in self.projects)
            ):
                self.reduction_state = "complete"
            elif any(
                (p.determine_reduction_state() == "complete" for p in self.projects)
            ):
                self.reduction_state = "incomplete"

    def _reduction_state_changed(self, new):
        if new == "complete":
            self.completion_date = datetime.datetime.now()


class DataReductionLogbookHandler(Handler):
    def closed(self, info, is_ok):
        info.ui.context["object"].closed()


class DataReductionLogbook(Loggable, ColumnSorterMixin):
    stats = Str

    loads = List
    oloads = List

    projects = List
    oprojects = List

    dvc = Instance(DVC)
    selected = Instance(DataReductionLoad, ())
    selected_project = Instance(ProjectDetail, ())
    selected_sample = Instance(SampleRecordView)
    search_entry = Str  # (auto_set=False, enter_set=True)
    search_entry_clear = Event

    project_search_entry = Str
    project_search_entry_clear = Event

    selected_project2 = Instance(ProjectDetail)

    sample_column_clicked = Event

    update = Event

    _cached_loads = None

    def set_stats(self, loaded_manifest=None):
        if loaded_manifest is None:
            loaded_manifest = []
            manifest_path = os.path.join(paths.meta_root, "dr_manifest.json")
            if os.path.isfile(manifest_path):
                with open(manifest_path, "r") as rfile:
                    loaded_manifest = json.load(rfile)
            for li in self.loads:
                if li.name in loaded_manifest:
                    li.examined = True

        self.stats = f"{len(loaded_manifest)}/{len(self.loads)}"

    def auto_examine(self):
        """
        for each load in all the loads in the db
        for each project in a given load
        for each sample in a given project in a given load
        for each analysis in a given sample in a given project in a given load
        """

        self.populate()

        self.dvc.backup_data_reduction_loads()
        drloads = self.dvc.get_data_reduction_loads()

        # backup drloads
        manifest_path = os.path.join(paths.meta_root, "dr_manifest.json")

        def get_dr_match(lname):
            return next((li for li in drloads if li["name"] == lname), None)

        def get_dr_proj(dr, pname):
            return next((p for p in dr["projects"] if p["name"] == pname), None)

        loaded_manifest = []
        if os.path.isfile(manifest_path):
            with open(manifest_path, "r") as rfile:
                loaded_manifest = json.load(rfile)

        self.set_stats(loaded_manifest=loaded_manifest)
        cnt = 0
        for li in self.loads:
            if cnt > 30:
                break

            if li.name in loaded_manifest:
                self.debug(f"skipping load {li.name}. already in manifest")
                continue

            cnt += 1
            loaded_manifest.append(li.name)
            # for lj in drloads:
            #     if lj["name"] == li.name:
            #         if lj["status"] == "complete":
            #             break
            # else:
            drload = get_dr_match(li.name)
            if drload and drload["reduction_state"] == "complete":
                continue

            print(f"examine load {li.name}")
            self.debug(f"examing load {li.name}")

            self.selected = li
            self._selected_changed()
            for p in self.selected.projects:
                if drload:
                    drproj = get_dr_proj(drload, p.name)
                    if drproj and drproj["reduction_state"] == "complete":
                        continue

                self.selected_project = p
                self._selected_project_changed(p)
                self.examine()

                # for s in self.selected_project.samples:
                #     self.selected_sample = s
                #     self._selected_sample_changed()
            payload = self.selected.tohistory()
            if drload:
                idx = drloads.index(drload)
                drloads.remove(drload)
                drloads.insert(idx, payload)
            else:
                self.selected.determine_status()
                payload = self.selected.tohistory()
                drloads.append(payload)

            self.save(payload=drloads)

            with open(manifest_path, "w") as wfile:
                json.dump(loaded_manifest, wfile, indent=4)

        # if not drload:
        #     payload = self.selected.tohistory()
        #     drloads.append(payload)
        # else:
        #
        # self.examine_projects(li.name)
        # self.save()
        # self.save()
        # with self.dvc.session_ctx():
        #     ls = []
        #     for li in self.dvc.get_loads():
        #         print(li)
        #         for lj in drloads:
        #             if lj["name"] == li.name:
        #                 if lj["status"] == "complete":
        #                     break
        #         else:
        #             # load is not complete according to dr json file.
        #             print(f'examine load {li.name}')
        #             self.debug(f'examing load {li.name}')
        #             self.selected = DataReductionLoad(record=li)
        #             self.examine(li.name)
        #             self.save()

    def examine(self, loadname=None):
        """examine the load and update the json file"""

        if loadname is None:
            loadname = self.selected.name

        if not self.selected:
            return

        self.debug(f"examining {loadname}")

        # get all the analyses for this load
        with self.dvc.session_ctx():
            l = self.dvc.get_load(loadname)

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

            anns = self.dvc.make_analyses(anss, warn=False, quick=True)
            for rname, gs in groupby_key(anns, key=lambda x: x.repository_identifier):
                repo = self.dvc.get_repository(rname)
                for sa, ais in groupby_key(list(gs), key=lambda x: x.identifier):
                    if self.selected:
                        ss = next(
                            (
                                s
                                for s in self.selected_project.samples
                                if s.identifier == sa
                            )
                        )
                        if ss.reduction_state == "complete":
                            continue

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

                    if self.selected:
                        # ss = next(
                        #     (
                        #         s
                        #         for s in self.selected_project.samples
                        #         if s.identifier == sa
                        #     )
                        # )
                        ss.reduction_state = reduction_state
            self.update = True

    def get_loads(self, projects=None):
        loads = self.dvc.get_data_reduction_loads()
        with self.dvc.session_ctx():
            ls = []
            for li in self.dvc.get_loads(projects=projects):
                la = DataReductionLoad(li)
                for lj in loads:
                    if lj["name"] == la.name:
                        la.set_history(lj)
                        break
                ls.append(la)

            self.loads = ls
            self.oloads = ls

    def get_projects(self):
        ps = sorted(
            [ProjectDetail(p) for p in self.dvc.get_projects()],
            key=lambda x: x.unique_id,
            reverse=True,
        )
        self.projects = ps
        self.oprojects = ps

    def populate(self):
        with self.dvc.session_ctx():
            self.get_loads()
            self.get_projects()

        self.set_stats()

    def save(self, payload=None, *args, **kw):
        self.debug("save")
        if payload is None:
            payload = [l.tohistory() for l in self.loads]
        self.dvc.save_data_reduction_loads(payload)

    def share(self):
        # self.save()
        self.dvc.share_data_reduction_loads()
        self.information_dialog("Data Reduction Log shared")

    def closed(self):
        if self.confirmation_dialog("Would you like to share your changes?"):
            self.share()

    def _search_entry_clear_fired(self):
        self.get_loads()

    # def _project_search_entry_clear_fired(self):
    #     self.get_projects()

    def _sample_column_clicked_fired(self, new):
        self._column_clicked_handled(new)

    def _project_search_entry_changed(self, new):
        if new:
            self.projects = fuzzyfinder(new, self.oprojects, "name")

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
                    if p.name
                    not in [
                        "REFERENCES",
                    ]
                ]

                ps = [next(pis) for g, pis in groupby_key(ps, key=lambda x: x.name)]
                # save = True

        ps = [ProjectDetail(p) for p in ps]
        if self.selected_project2:
            ps = [p for p in ps if p.name == self.selected_project2.name]
            self.selected_project = ps[0]
        # print(ps)
        self.selected.projects = ps
        # if save:
        #     self.save()
        #     self.dvc.clear_data_reduction_loads_cache()

    def _selected_project2_changed(self, new):
        self.get_loads(projects=[new.name])

    def _selected_project_changed(self, new):
        with self.dvc.session_ctx() as sess:
            ls = []
            for li in self.dvc.get_labnumbers(
                projects=[new.name], loads=[self.selected.name]
            ):
                if li.analyzed:
                    loads = self.dvc.get_data_reduction_loads()
                    r = LabnumberRecordViewDRDetai(li)
                    for drl in loads:
                        for drp in drl["projects"]:
                            for drs in drp["samples"]:
                                if drs["identifier"] == li.identifier:
                                    r.reduction_state = drs["reduction_state"]
                                    break

                    ls.append(r)
            self.selected.samples = ls
            self.selected_project.samples = ls

    def traits_view(self):
        grp = BorderVGroup(
            HGroup(
                UItem("search_entry"), icon_button_editor("search_entry_clear", "clear")
            ),
            # HGroup(UItem("stats")),
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
            label="Loads",
        )

        grp1 = BorderVGroup(
            HGroup(
                UItem("project_search_entry"),
                icon_button_editor("project_search_entry_clear", "clear"),
            ),
            UItem(
                "projects",
                editor=TabularEditor(
                    selected="selected_project2",
                    stretch_last_section=False,
                    adapter=ProjectAdapter(),
                ),
            ),
            label="Project",
        )
        v = View(
            VSplit(
                HGroup(grp, grp1),
                HSplit(
                    VGroup(
                        BorderVGroup(
                            UItem("object.selected.reduction_state"), label="Status"
                        ),
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
                                update="update",
                                editable=False,
                                stretch_last_section=False,
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
            ),
            # UItem('object.selected_project.samples',
            #       editor=TabularEditor(adapter=SampleAdapter()))),
            width=1200,
            toolbar=ToolBar(
                Action(name="Save", image=icon("database_save"), action="save"),
                Action(name="Share", image=icon("share"), action="share"),
                Action(
                    name="History",
                    image=icon("history"),
                    action="examine",
                    enabled_when="object.selected",
                ),
                Action(name="Auto Examine", action="auto_examine"),
            ),
            title="Data Reduction Log",
            handler=DataReductionLogbookHandler(),
            resizable=True,
        )
        return v


if __name__ == "__main__":
    paths.build("~/PychronDev")
    dr = DataReductionLogbook(
        dvc=get_dvc(host="localhost", username="root", password="argon4039")
    )
    # dr.auto_examine()
    dr.populate()
    dr.configure_traits()
# ============= EOF =============================================
