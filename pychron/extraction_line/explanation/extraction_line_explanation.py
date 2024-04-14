# ===============================================================================
# Copyright 2011 Jake Ross
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ===============================================================================

# =============enthought library imports=======================
from traits.api import HasTraits, Any, Event, List, Bool, Property, Int
from traitsui.api import View, Item, Handler, TabularEditor
from traitsui.tabular_adapter import TabularAdapter


# =============standard library imports ========================

# =============local library imports  ==========================


class ELEHandler(Handler):
    def init(self, info):
        if not info.initialized:
            info.object.selection_ok = True
        return True


class ExplanationAdapter(TabularAdapter):
    columns = [
        ("Name", "name"),
        ("Description", "description"),
        ("State", "state"),
        ("Lock", "lock"),
        ("Actuations", "actuations"),
        ("Last", "last_actuation"),
    ]

    lock_text = Property
    state_text = Property
    font = "12"
    name_width = Int(40)
    description_width = Int(175)
    state_width = Int(50)
    lock_width = Int(40)

    def get_bg_color(self, obj, trait, row, column):
        item = self.item
        color = "white"
        #         color='#0000FF'
        if item.software_lock:
            color = "#CCE5FF"
        elif item.state:
            color = "lightgreen"

        return color

    def _get_lock_text(self):
        return "Yes" if self.item.software_lock else "No"

    def _get_state_text(self):
        return "Open" if self.item.state else "Closed"


class ExtractionLineExplanation(HasTraits):
    """ """

    explanable_items = List
    show_hide = Event
    label = Property(depends_on="identify")

    identify = Bool(False)
    selected = Any
    selection_ok = False
    refresh_needed = Event

    def _get_label(self):
        return "Hide All" if self.identify else "Show All"

    def refresh(self):
        self.refresh_needed = True

    def load(self, switches):
        """ """

        vs = [s for s in switches.values() if s.explain_enabled]
        self.explanable_items.extend(vs)

    def traits_view(self):
        """ """
        v = View(
            Item(
                "explanable_items",
                editor=TabularEditor(
                    auto_update=True,
                    adapter=ExplanationAdapter(),
                    editable=False,
                    refresh="refresh_needed",
                    selected="selected",
                ),
                style="custom",
                show_label=False,
            ),
            width=500,
            height=500,
            id="pychron.explanation",
            resizable=True,
            title="Explanation",
        )
        return v
