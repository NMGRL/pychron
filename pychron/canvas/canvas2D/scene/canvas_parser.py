# ===============================================================================
# Copyright 2011 Jake Ross
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
# ===============================================================================

# ============= enthought library imports =======================

# ============= standard library imports ========================
import yaml

from pychron.canvas.canvas2D.scene.primitives.connections import Connection
from pychron.canvas.canvas2D.scene.primitives.valves import ManualSwitch, Switch, Valve
from pychron.core.xml.xml_parser import XMLParser


# ============= local library imports  ==========================
from pychron.core.yaml import yload


def get_volume(elem, tag="volume", default=0):
    """
    get volume tag from xml
    """
    vol = elem.find(tag)
    if vol is not None:
        vol = float(vol.text.strip())
    else:
        vol = default
    return vol


class CanvasParser(XMLParser):
    """ """

    pass


# ============= EOF ====================================
#
# class Text(object):
#     def __init__(self, t):
#         self.text = t
#
#
# class Element(object):
#     def __init__(self, obj):
#         self._obj = obj
#         if obj:
#             self.text = str(self._obj['name'])
#             self.translation = Text(self._obj['translation'])
#             self.description = str(self._obj.get('description', ''))
#
#     def find(self, key):
#         if self._obj:
#             if key == 'translation':
#                 ret = self.translation
#             elif key == 'description':
#                 ret = self.description
#             else:
#                 ret = Element(self._obj.get(key))
#             return ret
#
#
# class YAMLCanvasParser(object):
#     def __init__(self, p, load=True):
#         self._path = p
#         if load:
#             self._yd = yload(p)
#
#     def get_elements(self, key):
#         es = []
#         if key in self._yd:
#             es = [Element(ei) for ei in self._yd[key]]
#         return es
#
#     def find(self, key):
#         if key in self._yd:
#             return Element(self._yd[key])
#
#     def get_root(self):
#         return self
#
#     def dump(self, scene):
#         obj = {}
#
#         def factory(i):
#             return {'name': i.name,
#                     'translation': '{},{}'.format(i.x, i.y)}
#
#         for klass, key in ((Switch, 'switch'), (Valve, 'valve'), (ManualSwitch, 'manualswitch')):
#             items = [factory(i) for i in scene.get_items(klass)]
#             obj[key] = items
#
#         for c in scene.get_items(Connection):
#             print(c, c.start, c.end)
#
#         with open(self._path, 'w') as wfile:
#             yaml.dump(obj, wfile)
