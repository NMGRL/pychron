# ===============================================================================
# Copyright 2020 ross
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
from traitsui.api import View, Item, UItem, HGroup, Heading, spring

from pychron.core.pychron_traits import BorderVGroup
from pychron.options.options import SubOptions
from pychron.pychron_constants import MAIN, APPEARANCE


class MainView(SubOptions):

    def traits_view(self):
        v = View(BorderVGroup(Item('basemap_uri_template', label='Base Map URI'),
                              label='Web Map Services'),
                 HGroup(spring, Heading('or'), spring),
                 BorderVGroup(Item('basemap_path'),
                              label='Local Raster'),
                 UItem('basemap_uri', style='custom'))
        return v


class AppearanceView(SubOptions):
    def traits_view(self):
        v = View(BorderVGroup(Item('symbol_size'),
                              Item('symbol_kind'),
                              Item('symbol_color')))
        return v


VIEWS = {MAIN.lower(): MainView, APPEARANCE.lower(): AppearanceView}

# ============= EOF =============================================
