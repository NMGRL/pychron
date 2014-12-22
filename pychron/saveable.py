# ===============================================================================
# Copyright 2012 Jake Ross
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
from traits.api import Bool
from traitsui.menu import Action
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.viewable import Viewable, ViewableHandler

class SaveableHandler(ViewableHandler):
    def save(self, info):
        info.object.save()

    def save_as(self, info):
        info.object.save_as()

    def apply(self, info):
        info.object.apply()

class Saveable(Viewable):
    handler_klass = SaveableHandler
    save_enabled = Bool(False)

SaveButton = Action(name='Save', action='save',
                                enabled_when='object.save_enabled')
SaveAsButton = Action(name='Save As', action='save_as')

SaveableButtons = [SaveButton,
                          SaveAsButton]
# ============= EOF =============================================
