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
from traitsui.api import Item, VGroup

from pychron.core.pychron_traits import BorderVGroup
from pychron.options.options import SubOptions
from pychron.pychron_constants import (
    IDEOGRAM,
    ISOCHRON,
    SPECTRUM,
    FLECK_PLATEAU_DEFINITION,
    MAHON_PLATEAU_DEFINITION,
)


# class ArArCalculationSubOptions(SubOptions):
#     def traits_view(self):
#         return self._make_view()


class IdeogramSubOptions(SubOptions):
    def traits_view(self):
        grp = BorderVGroup(
            Item("probability_curve_kind", label="Probability Curve Method"),
            Item("mean_calculation_kind", label="Mean Calculation Method"),
            Item("error_calc_method", label="Error Calculation Method"),
        )

        return self._make_view(grp)


PLAT_GROUP = BorderVGroup(
    Item(
        "plateau_method",
        tooltip="Fleck 1977={}\n"
        "Mahon 1996={}".format(FLECK_PLATEAU_DEFINITION, MAHON_PLATEAU_DEFINITION),
        label="Method",
    ),
    Item("pc_nsteps", label="Num. Steps", tooltip="Number of contiguous steps"),
    Item(
        "pc_gas_fraction",
        label="Min. Gas%",
        tooltip="Plateau must represent at least Min. Gas% release",
    ),
    label="Plateau",
)


class SpectrumSubOptions(SubOptions):
    def traits_view(self):
        integrated = BorderVGroup(
            Item("integrated_include_omitted", label="Include Omitted"),
            label="Integrated",
        )
        grp = VGroup(PLAT_GROUP, integrated)
        return self._make_view(grp)


class IsochronSubOptions(SubOptions):
    def traits_view(self):
        filtering = BorderVGroup(
            Item("isochron_omit_non_plateau", label="Omit Non Plateau"),
            Item("isochron_exclude_non_plateau", label="Exclude Non Plateau"),
            label="Filtering",
        )
        grp = VGroup(PLAT_GROUP, filtering)
        return self._make_view(grp)


VIEWS = {
    SPECTRUM.lower(): SpectrumSubOptions,
    IDEOGRAM.lower(): IdeogramSubOptions,
    ISOCHRON.lower(): IsochronSubOptions,
}
# ============= EOF =============================================
