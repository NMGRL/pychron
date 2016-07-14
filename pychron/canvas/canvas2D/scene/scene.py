# ===============================================================================
# Copyright 2012 Jake Ross
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
from traits.api import HasTraits, List, on_trait_change, Any, Event
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.canvas.canvas2D.scene.primitives.primitives import Primitive
from pychron.canvas.canvas2D.scene.layer import Layer
from canvas_parser import CanvasParser


class Scene(HasTraits):
    layers = List
    overlays = List
    parser = None
    selected = Any
    layout_needed = Event
    font = None

    _xrange = -1, 1
    _yrange = -1, 1

    def set_canvas(self, c):
        for li in self.layers:
            for ci in li.components:
                ci.set_canvas(c)

    def reset_layers(self):

        self.set_canvas(None)
        for li in self.layers:
            li.destroy()

        self.layers = [Layer(name='0'), Layer(name='1')]

    def load(self, pathname):
        """
        """
        pass

    def render_overlays(self, gc, canvas):
        x1, x2 = canvas.get_mapper_limits('index')
        y1, y2 = canvas.get_mapper_limits('value')

        bounds = x1, x2, y1, y2
        self._render(gc, canvas, self.overlays, bounds)

    def render_components(self, gc, canvas):
        # only render components within the current bounds.

        x1, x2 = canvas.get_mapper_limits('index')
        y1, y2 = canvas.get_mapper_limits('value')

        bounds = x1, x2, y1, y2
        self._render(gc, canvas, (ci for li in self.layers if li.visible
                                  for ci in li.components
                                  if ci.scene_visible and ci.visible), bounds)

    def request_layout(self):
        for i in self.iteritems():
            i.request_layout()

    def iteritems(self, exclude=None, klass=None):
        if exclude is None:
            exclude = tuple()

        if not isinstance(exclude, (list, tuple)):
            exclude = (exclude,)

        def _test(cc):
            return type(cc) not in exclude

        if klass:
            def btest(cc):
                return isinstance(cc, klass) and _test(cc)

            test = btest
        else:
            test = _test

        return (ci for li in self.layers
                for ci in li.components
                if test(ci))

    def get_items(self, klass=None):
        #         return [ci for li in self.layers
        #                 for ci in li.components
        #                     if isinstance(ci, klass)]
        #
        comps = (ci for li in self.layers
                 for ci in li.components)
        if klass:
            return [ci for ci in comps if isinstance(ci, klass)]
        else:
            return list(comps)

    def get_item(self, name, layer=None, klass=None):
        def test(la):
            nb = la.name == str(name)
            ib = la.identifier == str(name)
            cb = True
            if klass is not None:
                cb = isinstance(la, klass)
            return cb and (nb or ib)

        layers = self.layers
        if layer is not None:
            layers = layers[layer:layer + 1]

        for li in layers:
            nn = next((ll for ll in li.components if test(ll)), None)
            if nn is not None:
                return nn
        else:
            for o in self.overlays:
                if test(o):
                    return o

    def add_item(self, v, layer=None):
        if layer is None:
            layer = -1
        if isinstance(layer, str):
            olayer = next((li for li in self.layers if li.name == layer), None)
            if olayer is None:
                layer = Layer(name=layer)
                self.layers.append(layer)
            else:
                layer = olayer
        else:

            n = len(self.layers)
            if layer > n - 1:
                self.layers.append(Layer(name='{}'.format(n)))

            layer = self.layers[layer]

        layer.add_item(v)

    def remove_klass(self, klass, layer=None):
        if layer is None:
            layers = self.layers
        else:
            layers = (self.layers[layer],)

        for li in layers:
            li.remove_klass(klass)

    def remove_item(self, v, layer=None):
        if layer is None:
            layers = self.layers
        else:
            layers = (self.layers[layer],)

        if isinstance(v, str):
            v = self.get_item(v)

        if v:
            for li in layers:
                li.remove_item(v)

    def pop_item(self, v, layer=None, klass=None):
        if layer is None:
            layers = self.layers
        else:
            layers = (self.layers[layer],)

        for li in layers:
            li.pop_item(v, klass=klass)

    def get_xrange(self):
        return self._xrange

    def get_yrange(self):
        return self._yrange

    # ===============================================================================
    # handlers
    # ===============================================================================
    def _selected_changed(self, name, old, new):
        if issubclass(type(new), Primitive):
            if issubclass(type(old), Primitive):
                old.set_selected(False)
            new.set_selected(True)

        self.layout_needed = True

    @on_trait_change('layers:visible')
    def _refresh(self):
        self.layout_needed = True

    # private
    def _render(self, gc, canvas, components, bounds):
        for ci in components:
            if ci.is_in_region(*bounds):
                if self.font:
                    ci.font = self.font
                ci.set_canvas(canvas)
                ci.render(gc)

    def _get_floats(self, elem, name):
        return map(float, elem.find(name).text.split(','))

    def _get_translation(self, cp, elem, name='translation'):
        x, y = elem.find(name).text.split(',')
        try:
            x = float(x)
        except ValueError:
            x = self._get_parameteric_translation(cp, x)

        try:
            y = float(y)
        except ValueError:
            y = self._get_parameteric_translation(cp, y)

        return x, y

    def _get_parameteric_translation(self, cp, tag):
        v = 0
        offset = 0
        if '+' in tag:
            tag, offset = tag.split('+')
        elif '-' in tag:
            tag, offset = tag.split('-')

        offset = int(offset)
        for p in cp.get_elements('param'):
            if p.text.strip() == tag:
                e = p.find('value')
                v = e.text.strip()

        return float(v) + offset

    def _make_color(self, c):
        if not isinstance(c, str):
            c = ','.join(map(str, map(int, c)))
            c = '({})'.format(c)
        return c

    def _get_canvas_parser(self, p=None):
        if p is not None:
            cp = CanvasParser(p)
            self.parser = cp
        elif self.parser:
            cp = self.parser

        return cp

    def _get_canvas_view_range(self, cp):
        xv = (-25, 25)
        yv = (-25, 25)
        #         cp = self._get_canvas_parser()
        tree = cp.get_tree()
        if tree:
            elm = tree.find('xview')
            if elm is not None:
                xv = map(float, elm.text.split(','))

            elm = tree.find('yview')
            if elm is not None:
                yv = map(float, elm.text.split(','))

        return xv, yv

# ============= EOF =============================================
