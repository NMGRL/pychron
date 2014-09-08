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
from pychron.core.ui import set_qt
set_qt()
# ============= enthought library imports =======================
from traits.api import HasTraits, Any, Str
from traitsui.api import View, VGroup, Readonly, UItem
#============= standard library imports ========================
import Image
import cStringIO
#============= local library imports  ==========================
from pychron.core.ui.image_editor import ImageEditor


class SnapshotView(HasTraits):
    image = Any
    local_path = Str
    remote_path = Str

    def set_image(self, l, r, im):
        self.local_path=l
        self.remote_path=r
        if im:
            buf = cStringIO.StringIO(im)
            buf.seek(0)
            try:
                img = Image.open(buf)
                self.image = img.convert('RGBA')
            except IOError:
                pass

    def traits_view(self):
        v=View(VGroup(VGroup(Readonly('local_path'),
                      Readonly('remote_path')),
               VGroup(UItem('image', editor=ImageEditor()))),
               title='Snapshot')
        return v


if __name__ == '__main__':
    sv=SnapshotView()
    with open('/Users/ross/Pychrondata_dev/data/snapshots/snapshot-001.jpg', 'rb') as fp:
        sv.set_image('a','b', fp.read())
    sv.configure_traits()
#============= EOF =============================================



