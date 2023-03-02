# ===============================================================================
# Copyright 2019 ross
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
from traits.api import Int, Bool
from traitsui.api import Item, Tabbed

from pychron.core.helpers.traitsui_shortcuts import okcancel_view
from pychron.core.pychron_traits import BorderVGroup
from pychron.core.ui.table_configurer import (
    TableConfigurer,
    TableConfigurerHandler,
    get_columns_group,
)


class AnalysisTableConfigurer(TableConfigurer):
    id = "analysis.table"
    limit = Int
    omit_invalid = Bool(True)

    # def __init__(self, *args, **kw):
    #     self.auto_set = True
    #     self.auto_set_str = 'font, columns[], cw_+'
    #     super(AnalysisTableConfigurer, self).__init__(*args, **kw)

    def _get_dump(self):
        obj = super(AnalysisTableConfigurer, self)._get_dump()
        obj["limit"] = self.limit
        obj["omit_invalid"] = self.omit_invalid

        return obj

    def _load_hook(self, obj):
        self.limit = obj.get("limit", 500)
        self.omit_invalid = obj.get("omit_invalid", True)

    def traits_view(self):
        widths_grp = self._get_column_width_group()
        v = okcancel_view(
            BorderVGroup(
                Tabbed(get_columns_group(), widths_grp),
                Item("omit_invalid", label="Hide Invalid Analyses"),
                Item(
                    "limit", tooltip="Limit number of displayed analyses", label="Limit"
                ),
                label="Limiting",
            ),
            buttons=["OK", "Cancel", "Revert"],
            title=self.title,
            handler=TableConfigurerHandler,
            width=300,
        )
        return v


# ============= EOF =============================================
