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
from traits.api import HasTraits, List
from traitsui.api import View, ListStrEditor, UItem
#============= standard library imports ========================
#============= local library imports  ==========================

class SnapshotView(HasTraits):
    paths = List
    name='Snapshots'
    def __init__(self, paths, *args, **kw):
        self.paths=paths
        super(SnapshotView, self).__init__(*args, **kw)

    def traits_view(self):
        v=View(UItem('paths', editor=ListStrEditor(horizontal_lines=True)))
        return v
#============= EOF =============================================



