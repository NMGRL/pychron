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
from traits.api import Any, Long, Date, Str, on_trait_change
from traitsui.api import View, UItem, VGroup
from traits.api import HasTraits
# ============= standard library imports ========================
import Image
import cStringIO
# ============= local library imports  ==========================
from pychron.core.ui.image_editor import ImageEditor
from pychron.core.ui.qt.camera_editor import CameraEditor
from pychron.envisage.tasks.base_editor import BaseTraitsEditor


class ImageModel(HasTraits):
    image = Any
    create_date = Date
    note = Str
    original_note = Str
    name = Str
    original_name = Str

    def __init__(self, blob=None, *args, **kw):
        super(ImageModel, self).__init__(*args, **kw)
        if blob:
            buf = cStringIO.StringIO(blob)
            buf.seek(0)
            try:
                img = Image.open(buf)
                self.image = img.convert('RGBA')
            except IOError, e:
                print 'snapshot view {}'.format(e)
                pass

        self.original_note = self.note
        self.original_name = self.name


class ImageTabEditor(BaseTraitsEditor):
    record_id = Long
    # image = Any

    @on_trait_change('model:[note, name]')
    def _handle_note_change(self):
        self.dirty = self.model.note != self.model.original_note or self.model.name != self.model.original_name
        if self.model.name != self.name:
            self.name = self.model.name

    def traits_view(self):
        v = View(VGroup(UItem('image', editor=ImageEditor(),
                              width=896, height=680)))
        return v


class CameraTab(BaseTraitsEditor):
    record_id = 'camera'

    def traits_view(self):
        v = View(UItem('camera', editor=CameraEditor(),
                       width=896, height=680))
        return v


# ============= EOF =============================================



