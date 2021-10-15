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
import csv
import os

from traits.api import (
    Str,
    Enum,
    Dict,
    File,
    Float,
    Range,
    List,
    HasTraits,
    Button,
    Int,
    Color,
    Bool,
    on_trait_change,
)
from traitsui.api import HGroup, Item, View, UItem
from traitsui.editors.api import EnumEditor
from traitsui.item import spring

from pychron.base_fs import BaseFS
from pychron.core.pychron_traits import BorderVGroup, BorderHGroup
from pychron.gis.views import VIEWS
from pychron.options.group.base_group_options import BaseGroupOptions
from pychron.options.options import BaseOptions, GroupMixin
from pychron.options.options_manager import OptionsManager
from pychron.pychron_constants import MAIN


def make_uri(url, t="xyz", zmax=19, zmin=5):
    return "type={}&url={}&zmax={}&zmin={}".format(t, url, zmax, zmin)


MARKERS = "Square", "Circle", "Pentagon", "Triangle", "Star"

PREDEFINED = {
    "OpenStreetMap": make_uri("https://tile.openstreetmap.org/{z}/{x}/{y}.png"),
    "OpenTopoMap": make_uri("http://a.tile.opentopomap.org/{z}/{x}/{y}.png"),
    "Stamen Terrain": make_uri("http://a.tile.stamen.com/terrain/{z}/{x}/{y}.png"),
    "Stamen Toner": make_uri("http://a.tile.stamen.com/toner/{z}/{x}/{y}.png"),
    "USGS Satellite": make_uri(
        "https://basemap.nationalmap.gov/arcgis/rest/services/"
        "USGSImageryOnly/MapServer/tile/{Z}/{Y}/{X}"
    ),
    "Hillshade": make_uri("http://tiles.wmflabs.org/hillshading/{z}/{x}/{y}.png"),
}


def extract_url(uri):
    args = uri.split("&")
    for a in args:
        if a.startswith("url="):
            return a[4:]


class GISGroup(BaseGroupOptions):
    marker = Enum(MARKERS)
    marker_size = Float
    angle = Range(0, 360, 0)
    opacity = Range(0.0, 1.0, 1.0)

    def todict(self):
        return {
            "name": self.marker.lower(),
            "size": str(self.marker_size),
            "color": self.color.name(),
            "angle": str(self.angle),
            "opacity": str(self.opacity),
        }

    def traits_view(self):
        g = BorderVGroup(
            HGroup(Item("marker"), UItem("marker_size"), Item("angle")),
            HGroup(UItem("color"), Item("opacity")),
            label="Group {}".format(self.group_id + 1),
        )
        v = View(g)
        return v


class LayerOption(HasTraits):
    path = File
    label = Str
    is_vector = False
    visible = Bool(True)
    remove_layer_button = Button("Remove Layer")

    @property
    def uri(self):
        raise NotImplementedError


class VectorLayerOption(LayerOption):
    is_vector = True
    size = Int
    kind = Enum(MARKERS)
    color = Color

    @property
    def symbolargs(self):
        return {
            "name": self.kind.lower(),
            "size": str(self.size),
            "color": self.color.name(),
        }


class CSVLayerOption(VectorLayerOption):
    provider = "delimitedtext"
    xfield = Str
    yfield = Str
    _fields = List

    def __init__(self, *args, **kw):
        super(CSVLayerOption, self).__init__(*args, **kw)
        self._parse()

    @property
    def uri(self):
        return "file://{}?delimiter={}&xField={}&yField={}".format(
            self.path, self.delimiter, self.xfield, self.yfield
        )

    def _parse(self):
        self.label = os.path.basename(self.path)
        with open(self.path, "r") as rfile:
            dialect = csv.Sniffer().sniff(rfile.read(1024))
            rfile.seek(0)
            reader = csv.DictReader(rfile, dialect=dialect)
            self._fields = reader.fieldnames
            self.delimiter = dialect.delimiter

    def traits_view(self):
        v = View(
            BorderVGroup(
                Item("path"),
                HGroup(
                    Item("xfield", editor=EnumEditor(name="_fields")),
                    Item("yfield", editor=EnumEditor(name="_fields")),
                ),
                BorderHGroup(
                    Item("kind"), Item("size"), UItem("color"), label="symbol"
                ),
                HGroup(UItem("remove_layer_button"), spring),
            )
        )
        return v


class OGRLayerOption(VectorLayerOption):
    provider = "ogr"

    def __init__(self, *args, **kw):
        super(OGRLayerOption, self).__init__(*args, **kw)
        if self.path:
            self.label = os.path.basename(self.path)

    @property
    def uri(self):
        return self.path

    def traits_view(self):
        v = View(
            BorderVGroup(
                Item("path"),
                BorderHGroup(
                    Item("kind"), Item("size"), UItem("color"), label="symbol"
                ),
                HGroup(UItem("remove_layer_button"), spring),
            )
        )
        return v


class GPXLayerOption(VectorLayerOption):
    provider = "gpx"
    kind = Str

    @property
    def uri(self):
        return "{}?type={}".format(self.path, self.kind)


class GISOptions(BaseOptions, GroupMixin, BaseFS):
    basemap_uri = Str(
        "type=xyz&url=https://tile.openstreetmap.org/{z}/{x}/{y}.png&zmax=19&zmin=5"
    )
    basemap_uri_template = Enum(list(PREDEFINED.keys()), transient=True)
    basemap_path = File

    layers = List
    # symbol_size = Int(5)
    # symbol_color = Color('blue')
    # symbol_kind = Enum('circle', 'square')
    group_options_klass = GISGroup
    grouping_attribute = Enum(
        "Material",
        "Sample",
        "Comment",
        "SubGroup",
        "Group Name",
        "Label Name",
        "No Grouping",
    )

    _predefined = Dict(transient=True)

    _suppress_template_update = False

    add_layer_button = Button("Add Layer", transient=True)

    def _get_tags(self):
        return ("layers",)

    def _add_layer_button_fired(self):
        p = self.open_file_dialog()
        if p:
            if p.endswith(".csv") or p.endswith(".txt"):
                # layer = CSVLayerOption(path=p)
                klass = CSVLayerOption
            elif p.endswith(".shp"):
                klass = OGRLayerOption
                # layer = OGRLayerOption(path=p)
            else:
                klass = LayerOption
                # layer = LayerOption(path=p)
            layer = klass(path=p)
            self.layers.append(layer)

    @on_trait_change("layers:remove_layer_button")
    def _handle_remove_layer(self, layer, name, old, new):
        self.layers.remove(layer)

    def get_feature_options(self, gid):
        n = len(self.groups)
        gid = gid % n
        fg = self.groups[gid]
        return fg.todict()

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

        self.basemap_uri = PREDEFINED.get(new, "")

    def initialize(self):
        self.subview_names = [MAIN, "Groups", "Layers"]

    def _get_subview(self, name):
        return VIEWS[name]


class GISOptionsManager(OptionsManager):
    id = "gis"
    options_klass = GISOptions

# ============= EOF =============================================
