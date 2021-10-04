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
from pychron.options.options import MainOptions, SubOptions, AppearanceSubOptions
from pychron.pychron_constants import MAIN, APPEARANCE
from traitsui.api import View, Item


class RegressionMainOptions(SubOptions):
    def traits_view(self):
        v = View(Item('regressor'))
        return v


class RegressionAppearance(AppearanceSubOptions):
    pass


class RegressionSubOptions(SubOptions):
    pass
    # def traits_view(self):
    #     v = View(Item('show_statistics'))
    #     return v


VIEWS = {MAIN.lower(): RegressionMainOptions,
         # 'regression series': RegressionSeriesSubOptions,
         APPEARANCE.lower(): RegressionAppearance,
         # 'display': DisplaySubOptions,
         # 'groups': GroupSubOptions
         }
# ============= EOF =============================================
