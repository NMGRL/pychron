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
from traits.api import Bool
# from pyface.tasks.editor import Editor
from pychron.loggable import Loggable
from pyface.tasks.traits_editor import TraitsEditor
#============= standard library imports ========================
#============= local library imports  ==========================

class BaseTraitsEditor(TraitsEditor, Loggable):
    dirty = Bool(False)
    #    ui = Instance(UI)
    #
    #    def create(self, parent):
    #        self.control = self._create_control(parent)

    def prepare_destroy(self):
        pass

    def destroy(self):
        self.prepare_destroy()
        super(BaseTraitsEditor, self).destroy()

        #self.ui.dispose()
        #self.control = self.ui = None

    def filter_invalid_analyses(self):
        pass

#
#    def _create_control(self, parent):
#        self.ui = self.edit_traits(kind='subpanel', parent=parent)
#        return self.ui.control

#============= EOF =============================================
