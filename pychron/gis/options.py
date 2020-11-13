# ===============================================================================
# Copyright 2020 ross
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

from traits.api import Str, Enum, Dict, File, Int, Color

from pychron.gis.views import VIEWS
from pychron.options.options import BaseOptions
from pychron.options.options_manager import OptionsManager
from pychron.pychron_constants import MAIN, APPEARANCE


def make_uri(url, t='xyz', zmax=19, zmin=5):
    return 'type={}&url={}&zmax={}&zmin={}'.format(t, url, zmax, zmin)


PREDEFINED = {"OpenStreetMap": make_uri('https://tile.openstreetmap.org/{z}/{x}/{y}.png'),
              'OpenTopoMap': make_uri('http://a.tile.opentopomap.org/{z}/{x}/{y}.png'),
              'Stamen Terrain': make_uri('http://a.tile.stamen.com/terrain/{z}/{x}/{y}.png'),
              'Stamen Toner': make_uri('http://a.tile.stamen.com/toner/{z}/{x}/{y}.png'),
              'USGS Satellite': make_uri('https://basemap.nationalmap.gov/arcgis/rest/services/'
                                         'USGSImageryOnly/MapServer/tile/{Z}/{Y}/{X}'),
              'Hillshade': make_uri('http://tiles.wmflabs.org/hillshading/{z}/{x}/{y}.png')
              }


def extract_url(uri):
    args = uri.split('&')
    for a in args:
        if a.startswith('url='):
            return a[4:]


class GISOptions(BaseOptions):
    basemap_uri = Str('type=xyz&url=https://tile.openstreetmap.org/{z}/{x}/{y}.png&zmax=19&zmin=5')
    basemap_uri_template = Enum(list(PREDEFINED.keys()), transient=True)
    basemap_path = File

    symbol_size = Int(5)
    symbol_color = Color('blue')
    symbol_kind = Enum('circle', 'square')

    _predefined = Dict(transient=True)

    _suppress_template_update = False

    def symbol_style(self):
        return {'name': self.symbol_kind, 'size': str(self.symbol_size), 'color': str(self.symbol_color.name())}

    def _basemap_uri_changed(self, new):
        n = extract_url(new)
        for k, v in PREDEFINED.items():
            if n == extract_url(v):
                self._suppress_template_update = True
                self.basemap_uri_template = k
                self._suppress_template_update = False

    def _basemap_path_changed(self, new):
        self.basemap_uri = new

    def _basemap_uri_template_changed(self, new):
        if self._suppress_template_update:
            return

        self.basemap_uri = PREDEFINED.get(new, '')

    def initialize(self):
        self.subview_names = [MAIN, APPEARANCE ]

    def _get_subview(self, name):
        return VIEWS[name]


class GISOptionsManager(OptionsManager):
    id = 'gis'
    options_klass = GISOptions

# ============= EOF =============================================
