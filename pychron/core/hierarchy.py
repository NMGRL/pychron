# ===============================================================================
# Copyright 2014 Jake Ross
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
import os
from traits.api import HasTraits, Button, Str, Int, Bool, Any, List
from traitsui.api import View, Item, UItem, HGroup, VGroup
# ============= standard library imports ========================
#============= local library imports  ==========================
class FilePath(HasTraits):
    name = Str
    root = Any
    root_path = Str

    @property
    def path(self):
        '''
            recursively assemble the path to this resourse
        '''
        if self.root:
            return os.path.join(self.root.path, self.name)
        elif self.root_path:
            return self.root_path
            # return '{}/{}'.format(self.root.path, self.name)
        else:
            return self.name


class Hierarchy(FilePath):
    children = List

    def _children_changed(self):
        for ci in self.children:
            ci.root = self

    def pwalk(self):
        for ci in self.children:
            print self.name, ci.path, ci.__class__.__name__
            if isinstance(ci, Hierarchy):
                ci.pwalk()
#============= EOF =============================================



