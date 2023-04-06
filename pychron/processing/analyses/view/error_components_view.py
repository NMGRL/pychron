# ===============================================================================
# Copyright 2014 Jake Ross
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
from traits.api import HasTraits, List, Str, Float
from traitsui.api import View, UItem, HGroup
from traitsui.editors.api import TableEditor
from traitsui.table_column import ObjectColumn

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.core.helpers.formatting import floatfmt
from pychron.core.pychron_traits import BorderVGroup
from pychron.core.ui.table_editor import myTableEditor
from pychron.processing.analyses.view.magnitude_editor import MagnitudeColumn
from pychron.pychron_constants import INTERFERENCE_KEYS


class ErrorComponent(HasTraits):
    name = Str
    value = Float

    def get_percent_value(self):
        return self.value / 100


class ErrorComponentsView(HasTraits):
    name = "Error Components"

    error_components = List
    error_components2 = List

    def __init__(self, an, *args, **kw):
        super(ErrorComponentsView, self).__init__(*args, **kw)
        self._load(an)

    def load(self, an):
        self._load(an)

    def _load(self, an):
        keys = [k for k in an.arar_mapping.values() if k in an.isotopes]

        def get_comp(age):
            es = []
            for k in keys:
                iso = an.isotopes[k]
                es.append(
                    ErrorComponent(
                        name=k, value=an.get_error_component(iso.name, uage=age)
                    )
                )

                d = "{} IC".format(k)
                es.append(
                    ErrorComponent(name=d, value=an.get_error_component(d, uage=age))
                )
                d = "{} bk".format(k)
                es.append(
                    ErrorComponent(name=d, value=an.get_error_component(d, uage=age))
                )

                d = "{} bs".format(k)
                es.append(
                    ErrorComponent(name=d, value=an.get_error_component(d, uage=age))
                )

            return es

        es = get_comp(an.uage_w_j_err)

        for k in INTERFERENCE_KEYS + ("J", "trapped_4036"):
            es.append(
                ErrorComponent(
                    name=k, value=an.get_error_component(k, uage=an.uage_w_j_err)
                )
            )

        self.error_components = es

        es = get_comp(an.uage_w_position_err)
        for k in INTERFERENCE_KEYS + ("Position", "trapped_4036"):
            es.append(
                ErrorComponent(
                    name=k, value=an.get_error_component(k, uage=an.uage_w_position_err)
                )
            )
        self.error_components2 = es

    def traits_view(self):
        cols = [
            ObjectColumn(name="name", label="Component"),
            MagnitudeColumn(name="value", label=""),
            ObjectColumn(
                name="value",
                label="Value",
                # width=100,
                format_func=lambda x: floatfmt(x, n=5),
            ),
        ]
        editor = myTableEditor(columns=cols, sortable=False, editable=False)

        e1 = BorderVGroup(UItem("error_components", editor=editor), label="With J Err.")
        e2 = BorderVGroup(
            UItem("error_components2", editor=editor), label="With Position Err."
        )
        v = View(HGroup(e1, e2))
        return v


# ============= EOF =============================================
