# ===============================================================================
# Copyright 2013 Jake Ross
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

from traits.api import HasTraits, Instance


# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.canvas.canvas2D.designer_extraction_line_canvas2D import DesignerExtractionLineCanvas2D
from pychron.canvas.canvas2D.extraction_line_canvas2D import ExtractionLineCanvas2D
from pychron.canvas.canvas2D.scene.canvas_parser import CanvasParser
from pychron.canvas.canvas2D.scene.extraction_line_scene import ExtractionLineScene
from pychron.canvas.canvas2D.scene.primitives.valves import Valve
from pychron.paths import paths


class Designer(HasTraits):
    scene = Instance(ExtractionLineScene, ())
    canvas = Instance(ExtractionLineCanvas2D)

    def _canvas_default(self):
        canvas = DesignerExtractionLineCanvas2D()
        return canvas

    def save_xml(self, p):
        if self.scene:
            # sync the canvas_parser with the
            # current scene and save
            if os.path.isfile(p):
                self._save_xml(p)
            else:
                self._construct_xml()

    def _save_xml(self, p):
        cp = CanvasParser(p)

        for tag in ('laser', 'stage', 'spectrometer'):
            for ei in cp.get_elements(tag):
                self._set_element_color(ei)
                self._set_element_translation(ei)

        for ei in cp.get_elements('valve'):
            self._set_element_translation(ei)

        for ei in cp.get_elements('connection'):
            # name = ei.text.strip()
            start = ei.find('start').text.strip()
            end = ei.find('end').text.strip()
            name = '{}_{}'.format(start, end)

            obj = self.scene.get_item(name)
            for t, tt in ((obj.clear_vorientation, 'vertical',),
                          (obj.clear_horientation, 'horizontal')):
                if t and obj.get('orientation') == tt:
                    ei.set('orientation', '')

                    # if obj.clear_vorientation and obj.orientation=='vertical':
                    # ei.set('orientation', '')
                    # if obj.clear_orientation and obj.orientation=='':
                    # ei.set('orientation', '')

        # p = os.path.join(os.path.dirname(p, ), 'test.xml')
        cp.save()

    def _set_element_translation(self, elem):
        def func(obj, trans):
            trans.text = '{},{}'.format(obj.x, obj.y)

        self._set_element_attr(func, elem, 'translation')

    def _set_element_color(self, elem):
        def func(obj, color):
            if color is not None:
                c = ','.join(map(lambda x: str(x),
                                 obj.default_color.toTuple()
                                 ))
                color.text = c

        self._set_element_attr(func, elem, 'color')

    def _set_element_attr(self, func, elem, tag):
        name = elem.text.strip()
        obj = self.scene.get_item(name)
        if obj is not None:
            func(obj, elem.find(tag))

    def _construct_xml(self):
        tags = {Valve: 'valve'}
        cp = CanvasParser()
        for elem in self.scene.iteritems():
            if type(elem) in tags:
                tag = tags[type(elem)]
                print 'adsfafd', tag, elem
            elif hasattr(elem, 'type_tag'):
                print 'fffff', elem.type_tag, elem

    def open_xml(self, p):
        #cp=CanvasParser(p)
        #print cp

        scene = ExtractionLineScene()
        self.canvas.scene = scene
        cp = os.path.join(os.path.dirname(p), 'canvas_config.xml')
        vp = os.path.join(paths.extraction_line_dir, 'valves.xml')
        scene.load(p, cp, vp, self.canvas)

        self.scene = scene

        # ============= EOF =============================================
