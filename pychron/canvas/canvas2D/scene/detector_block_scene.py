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
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.canvas.canvas2D.scene.primitives.detector_block import Detector
from pychron.canvas.canvas2D.scene.scene import Scene
from pychron.core.xml.xml_parser import XMLParser


class DetectorBlockScene(Scene):
    def set_detector_offset(self, det, v):
        obj = self.get_item(det, klass=Detector)
        if obj is not None:
            obj.offset_y = v
            obj.request_layout()

    def set_detector_deflection(self, det, v):
        obj = self.get_item(det, klass=Detector)
        if obj is not None:
            obj.deflection = v
            obj.request_layout()

    # loading
    def load(self, path):
        self.reset_layers()
        parser = XMLParser(path)
        self._load_detectors(parser)

    def _load_detectors(self, parser):
        for det in parser.get_elements('detector'):
            self._add_detector(det)

    def _add_detector(self, elem):
        x, y = self._get_floats(elem, 'translation')
        mid, mad = self._get_floats(elem, 'deflection_range')
        w, h = 5, 5
        name = elem.text.strip()
        det = Detector(x, y,
                       width=w, height=h,
                       min_deflection=mid,
                       max_deflection=mad,
                       name=name)
        self.add_item(det)

# ============= EOF =============================================
