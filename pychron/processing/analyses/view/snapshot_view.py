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
from traits.api import HasTraits, List, Str, Instance, Any
from traitsui.api import View, UItem, VGroup, TabularEditor, HSplit, Item
# ============= standard library imports ========================
import StringIO
import Image
from numpy import array
#============= local library imports  ==========================
from traitsui.tabular_adapter import TabularAdapter
from pychron.core.ui.image_editor import ImageEditor


class SnapshotAdapter(TabularAdapter):
    columns = [('Name', 'name')]


class Snapshot(HasTraits):
    path = Str
    remote_path = Str
    image = Str
    name = Str


class SnapshotView(HasTraits):
    names = List
    name = 'Snapshots'
    selected = Instance(Snapshot)
    selected_path = Str
    selected_remote_path = Str
    selected_image = Any

    def _selected_changed(self, new):
        if new:
            self.selected_path = new.path
            self.selected_remote_path = new.remote_path
            if new.image:
                try:
                    buf = StringIO.StringIO(new.image)
                    buf.seek(0)
                    img = Image.open(buf)
                    self.selected_image = img.convert('RGBA')
                except IOError:
                    self.selected_image = array([])

            else:
                self.selected_image = array([])


    def __init__(self, snapshots, *args, **kw):
        self.snapshots = snapshots
        super(SnapshotView, self).__init__(*args, **kw)

    def traits_view(self):
        v = View(HSplit(UItem('snapshots', editor=TabularEditor(adapter=SnapshotAdapter(),
                                                                editable=False,
                                                                selected='selected'),
                              width=200),
                        VGroup(Item('selected_path', label='Local', style='readonly'),
                               Item('selected_remote_path',label='Remote', style='readonly'),
                               VGroup(UItem('selected_image',
                                     width=500,
                                     editor=ImageEditor())))))
        return v

#============= EOF =============================================



