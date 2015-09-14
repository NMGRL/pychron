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
from traits.api import HasTraits, Int, List
from traitsui.api import View, UItem, Item, VGroup, Controller
# ============= standard library imports ========================
import os
# ============= local library imports  ==========================
from traitsui.editors.check_list_editor import CheckListEditor
from pychron.paths import paths
from pychron.persistence_loggable import PersistenceMixin


def formatter(x):
    return x.lower().replace(' ', '_')


class FindReferencesConfigModel(HasTraits, PersistenceMixin):
    analysis_types = List
    threshold = Int

    pattributes = ('analysis_types', 'threshold')

    @property
    def persistence_path(self):
        return os.path.join(paths.hidden_dir, 'find_references_config')

    @property
    def formatted_analysis_types(self):
        return map(formatter, self.analysis_types)


class FindReferencesConfigView(Controller):
    def init(self, info):
        self.model.load()

    def closed(self, info, is_ok):
        if is_ok:
            self.model.dump()

    def traits_view(self):
        v = View(VGroup(UItem('analysis_types',
                              style='custom',
                              editor=CheckListEditor(values=['Blank Unknown', 'Blank Air',
                                                             'Blank Cocktail',
                                                             'Air', 'Cocktail'])),
                        Item('threshold', label='Threshold (hrs)')),
                 buttons=['OK', 'Cancel'],
                 kind='livemodal')

        return v

# ============= EOF =============================================
