# ===============================================================================
# Copyright 2017 ross
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
from traitsui.api import View, Item

from pychron.options.options import MainOptions, SubOptions, AppearanceSubOptions, TitleSubOptions, GroupSubOptions
from pychron.pychron_constants import MAIN, APPEARANCE


class RegressionSeriesMainOptions(MainOptions):
    pass


class RegressionSeriesSubOptions(SubOptions):
    def traits_view(self):
        v = View(Item('show_statistics'))
        return v


class RegressionSeriesAppearance(AppearanceSubOptions):
    pass


class CalculationSubOptions(SubOptions):
    pass


class DisplaySubOptions(TitleSubOptions):
    pass


VIEWS = {MAIN.lower(): RegressionSeriesMainOptions,
         'regression series': RegressionSeriesSubOptions,
         APPEARANCE.lower(): RegressionSeriesAppearance,
         'display': DisplaySubOptions,
         'groups': GroupSubOptions}

# ============= EOF =============================================
