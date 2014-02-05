#===============================================================================
# Copyright 2013 Jake Ross
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#===============================================================================

#============= enthought library imports =======================
from traits.api import List, Property, Int

#============= standard library imports ========================
#============= local library imports  ==========================

#============= EOF =============================================
from traitsui.tabular_adapter import TabularAdapter


class BrowserAdapter(TabularAdapter):
    font = 'arial 10'
    all_columns = List
    all_columns_dict = Property

    def _get_all_columns_dict(self):
        return dict(self.all_columns)


class ProjectAdapter(BrowserAdapter):
    columns = [('Name', 'name')]


class SampleAdapter(BrowserAdapter):
    columns = [('Sample', 'name'),
               ('Identifier', 'labnumber'),
               ('Material', 'material')]
    all_columns = [('Sample', 'name'),
                   ('Identifier', 'labnumber'),
                   ('Material', 'material'),
                   ('Irradiation','irradiation'),
                   ('Level', 'irradiation_and_level'),
                   ('Irrad. Pos.','irradiation_pos')]
    #     material_text = Property
    odd_bg_color = 'lightgray'

    name_width = Int(150)
    labnumber_width = Int(75)
    material_width = Int(100)