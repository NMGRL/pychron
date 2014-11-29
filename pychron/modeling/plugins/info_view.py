# ===============================================================================
# Copyright 2011 Jake Ross
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
# ===============================================================================

# ============= enthought library imports =======================
from traits.api import HasTraits, Instance
from traitsui.api import View, Item
# ============= standard library imports ========================

# ============= local library imports  ==========================
from pychron.modeling.model_data_directory import ModelDataDirectory

# ============= views ===================================
class InfoView(HasTraits):
    data_directory = Instance(ModelDataDirectory)

    def selected_update(self, obj, name, old, new):
        if not isinstance(new, ModelDataDirectory):
            try:
                new = new[0]
            except (IndexError, TypeError):
                return
        self.data_directory = new

    def traits_view(self):
        v = View(
               Item('data_directory',
                     style='custom',
                     show_label=False),
                 )
        return v
