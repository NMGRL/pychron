# ===============================================================================
# Copyright 2021 ross
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
from traits.api import HasTraits, Str, List, Color, Button
from traitsui.api import VGroup, UItem, Item, HGroup
from traitsui.editors import TabularEditor
from traitsui.tabular_adapter import TabularAdapter

from pychron.core.helpers.traitsui_shortcuts import okcancel_view
from pychron.core.pychron_traits import BorderVGroup


class LabelAdapter(TabularAdapter):
    columns = [("Name", "name")]

    def get_bg_color(self, obj, trait, row, column=0):
        return self.item.color


class Label(HasTraits):
    name = Str
    color = Color

    def __init__(self, gh_label, *args, **kw):
        super(Label, self).__init__(*args, **kw)
        self.name = gh_label["name"]
        self.color = int(gh_label["color"], 16)


class ExperimentNote(HasTraits):
    note = Str
    title = Str
    labels = List
    applied_labels = List

    selected_labels = List
    selected_applied_labels = List

    add_label_button = Button("Add Label")
    remove_label_button = Button("Remove Label")

    def _add_label_button_fired(self):
        if self.selected_labels:
            s = self.selected_labels[:]
            for si in self.selected_labels:
                if si in self.applied_labels:
                    s.remove(si)

            if s:
                self.applied_labels.extend(s)

    def _remove_label_button_fired(self):
        if self.selected_applied_labels:
            for label in self.selected_applied_labels:
                self.applied_labels.remove(label)

    def set_labels(self, labels):
        self.labels = [Label(label) for label in labels]

    def to_issue(self):
        issue = {
            "title": self.title or "No Title Provided",
            "labels": [la.name for la in self.applied_labels],
            "body": self.note,
        }
        return issue

    def traits_view(self):
        applied = VGroup(
            UItem("remove_label_button"),
            UItem(
                "applied_labels",
                editor=TabularEditor(
                    adapter=LabelAdapter(),
                    multi_select=True,
                    selected="selected_applied_labels",
                ),
            ),
        )
        avaliable = VGroup(
            UItem("add_label_button"),
            UItem(
                "labels",
                editor=TabularEditor(
                    adapter=LabelAdapter(),
                    multi_select=True,
                    selected="selected_labels",
                ),
            ),
        )

        labels = HGroup(avaliable, applied)

        grp = VGroup(
            Item("title"),
            BorderVGroup(UItem("note", style="custom", width=500), label="Note"),
            labels,
        )
        v = okcancel_view(grp, "Experiment Note")
        return v


# ============= EOF =============================================
