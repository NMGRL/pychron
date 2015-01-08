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
from traits.api import HasTraits, Str, Int, Bool, Any, Float, Property, on_trait_change, Instance
from traitsui.api import View, UItem, Item, HGroup, VGroup
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.core.ui.qt.camera_editor import CameraEditor
from pychron.image.toupcam.api import start, get_camera


class Camera(HasTraits):
    _data = None
    def __init__(self):
        super(Camera, self).__init__()
        cam = get_camera()
        start(cam, self._callback)

    def _callback(self, data):
        self._data = data

    def get_image_data(self, *args, **kw):
        return self._data


class D(HasTraits):
    camera = Instance(Camera, ())

    def traits_view(self):
        v = View(UItem('camera', editor=CameraEditor()),
                 width=680, height=510)
        return v


if __name__ == '__main__':
    D().configure_traits()

# ============= EOF =============================================



