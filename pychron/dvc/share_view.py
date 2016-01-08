# ===============================================================================
# Copyright 2016 Jake Ross
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
from traits.api import HasTraits, Str, Int, Bool, Any, Float, Property, \
    on_trait_change, Instance, Button
from traitsui.api import View, UItem, Item, HGroup, VGroup
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.loggable import Loggable


class ShareMetaDBView(Loggable):
    dvc = Instance('pychron.dvc.dvc.DVC')

    message = Str
    share_button = Button

    # handlers
    def _share_button_fired(self):
        self.debug('Share meta db')
        repo = self.dvc.meta_repo
        p = self.dvc.db.path
        if repo.add_paths(p):
            repo.commit(self.message)
            repo.push()
        else:
            self.information_dialog('No changes to share')

    def traits_view(self):
        v = View(VGroup(UItem('message', style='custom'),
                        HGroup(UItem('share_button', enabled_when='message'))),
                 title='Share Meta DB')
        return v


# ============= EOF =============================================



