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
from chaco.default_colormaps import color_map_name_dict
from traitsui.api import Item, HGroup, VGroup, Readonly, EnumEditor

from pychron.core.pychron_traits import BorderVGroup
from pychron.options.options import SubOptions, AppearanceSubOptions
from pychron.pychron_constants import (
    MAIN,
    APPEARANCE,
    LEAST_SQUARES_1D,
    WEIGHTED_MEAN_1D,
    BRACKETING,
    NN,
    MATCHING,
)


class FluxSubOptions(SubOptions):
    def traits_view(self):
        calc_grp = VGroup(
            Item("selected_monitor", label="Flux Const."),
            Readonly(
                "lambda_k",
                format_func=lambda x: "{:0.3u}".format(x),
                label="Total \u03BB K",
            ),
            Readonly("monitor_age"),
            BorderVGroup(
                Item("model_kind", label="Kind"),
                Item("error_kind", label="Mean J Error"),
                Item("predicted_j_error_type", label="Predicted J Error"),
                Item("use_weighted_fit"),
                Item(
                    "least_squares_fit",
                    visible_when='model_kind=="{}"'.format(LEAST_SQUARES_1D),
                ),
                Item(
                    "one_d_axis",
                    label="Axis",
                    visible_when='model_kind in ("{}","{}")'.format(
                        LEAST_SQUARES_1D, WEIGHTED_MEAN_1D
                    ),
                ),
                Item(
                    "n_neighbors",
                    label="N. Neighbors",
                    visible_when='model_kind == "{}"'.format(NN),
                ),
                label="Model",
            ),
            VGroup(
                HGroup(
                    Item("use_monte_carlo", label="Use"),
                    Item(
                        "monte_carlo_ntrials",
                        label="N. Trials",
                        tooltip="Number of trials to perform monte carlo simulation",
                    ),
                ),
                Item(
                    "position_error",
                    label="Position Error (Beta)",
                    tooltip="Set this value to the radius (same units as hole XY positions) of the "
                    "irradiation hole. "
                    'This is to test "monte carloing" the irradiation geometry',
                ),
                show_border=True,
                visible_when='model_kind not in ("{}", "{}", "{}")'.format(
                    MATCHING, BRACKETING, NN
                ),
                label="Monte Carlo",
            ),
            show_border=True,
            label="Calculations",
        )

        grp = VGroup(Item("plot_kind"), calc_grp)

        return self._make_view(grp)


class FluxAppearanceSubOptions(AppearanceSubOptions):
    def traits_view(self):
        twodgrp = VGroup(
            HGroup(
                Item(
                    "color_map_name",
                    label="Color Map",
                    editor=EnumEditor(values=sorted(color_map_name_dict.keys())),
                ),
                Item("levels"),
            ),
            visible_when='plot_kind=="2D"',
            label="Options",
            show_border=True,
        )
        onedgrp = VGroup(
            Item("marker_size"),
            visible_when='plot_kind=="1D"',
            label="Options",
            show_border=True,
        )
        scalegrp = VGroup(
            Item(
                "flux_scalar",
                label="Scale",
                tooltip="Multiple flux by Scale. FOR DISPLAY ONLY",
            )
        )
        return self._make_view(VGroup(twodgrp, onedgrp, scalegrp))


VIEWS = {MAIN.lower(): FluxSubOptions, APPEARANCE.lower(): FluxAppearanceSubOptions}
# ============= EOF =============================================
