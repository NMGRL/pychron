# ===============================================================================
# Copyright 2024 ross
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
from locale import format_string

from click import style
from pyface.tasks.traits_dock_pane import TraitsDockPane
from pyface.tasks.traits_task_pane import TraitsTaskPane
from traitsui.api import (
    View,
    UItem,
    InstanceEditor,
    TableEditor,
    EnumEditor,
    ListEditor,
    ButtonEditor,
)
from traitsui.extras.checkbox_column import CheckboxColumn
from traitsui.table_column import ObjectColumn


class BakeoutGraphPane(TraitsTaskPane):

    def traits_view(self):
        v = View(UItem("graph", style="custom", editor=InstanceEditor()))
        return v


class BakeoutControlPane(TraitsDockPane):
    name = "Controls"
    id = "pychron.bakeout.control"

    def traits_view(self):
        cols = [
            # CheckboxColumn(name='display'),
            CheckboxColumn(name="enabled"),
            ObjectColumn(name="name", editable=False),
            ObjectColumn(name="setpoint", format="%0.3f", editable=False),
            ObjectColumn(name="temperature", format="%0.3f", editable=False),
            ObjectColumn(name="duty_cycle", format="%0.3f", editable=False),
            CheckboxColumn(name="overtemp", editable=False),
            # ObjectColumn(name='clear_overtemp',
            #              style='custom',
            #              editor=ButtonEditor(),
            #              label='Clear Over Temp.'),
            # ObjectColumn(name='temperature_address', editable=False),
            # ObjectColumn(name='duty_cycle_address', editable=False),
            # ObjectColumn(name='setpoint_address', editable=False),
        ]

        edit_view = View(
            UItem("object.temperature"),
            UItem("object.clear_overtemp", style="custom"),
        )

        v = View(
            UItem(
                "object.controller.configuration",
                editor=EnumEditor(name="object.controller.configurations"),
                width=200,
            ),
            UItem(
                "object.controller.channels",
                style="custom",
                editor=TableEditor(
                    columns=cols,
                    selection_mode="rows",
                    edit_view=edit_view,
                    orientation="vertical",
                    selected="object.controller.selected_channel",
                ),
            ),
            # UItem(
            #     'object.controller.channels',
            #     editor=ListEditor(style='custom')
            # )
        )
        return v


# ============= EOF =============================================
