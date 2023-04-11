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
from traitsui.api import UItem, TableEditor

# ============= standard library imports ========================
# ============= local library imports  ==========================
from traitsui.handler import Controller
from traitsui.table_column import ObjectColumn

from pychron.core.helpers.traitsui_shortcuts import okcancel_view
from pychron.spectrometer.field_table import FieldTable


class MagnetFieldTableView(Controller):
    model = FieldTable

    def closed(self, info, is_ok):
        if is_ok:
            self.model.save()

    def traits_view(self):
        # self.model.load_mftable(True)

        cols = [ObjectColumn(name="isotope", editable=False)]

        for di in self.model.detector_names:
            cols.append(ObjectColumn(name=di, format="%0.5f", label=di))

        v = okcancel_view(
            UItem("items", editor=TableEditor(columns=cols, sortable=False)),
            title="Edit Magnet Field Table",
        )
        return v


if __name__ == "__main__":
    from pychron.spectrometer.molecular_weights import MOLECULAR_WEIGHTS as molweights

    m = FieldTable(molweights=molweights)
    mv = MagnetFieldTableView(model=m)
    mv.configure_traits()

# ============= EOF =============================================
