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
from traitsui.api import VGroup, Item, Readonly

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.core.pychron_traits import BorderVGroup
from pychron.options.options import SubOptions, AppearanceSubOptions


class VerticalFluxSubOptions(SubOptions):
    def traits_view(self):
        vg = VGroup(
            Item("use_j", label="Use J"),
            BorderVGroup(
                Item("selected_monitor", label="Flux Const."),
                Readonly("lambda_k", label="Total \u03BB K"),
                Readonly("monitor_age", label="Monitor Age"),
                label="Monitor",
                enabled_when="use_j",
            ),
        )
        return self._make_view(vg)


class VerticalFluxAppearanceSubOptions(AppearanceSubOptions):
    pass


VIEWS = {"main": VerticalFluxSubOptions, "appearance": VerticalFluxAppearanceSubOptions}
# ============= EOF =============================================
