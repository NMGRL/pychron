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
from operator import attrgetter

import folium
from PyQt5.QtWebEngineWidgets import QWebEngineView
from traits.api import HasTraits, Instance, Str, Event, on_trait_change, Float, Range
from traitsui.api import View, Item, HGroup, VGroup
from traitsui.item import UReadonly, UItem
from traitsui.qt.basic_editor_factory import BasicEditorFactory
from traitsui.qt.editor import Editor

from pychron.core.helpers.iterfuncs import groupby_key
from pychron.pipeline.plot.editors.base_editor import BaseEditor


class _WebViewEditor(Editor):
    refresh = Event

    def init(self, parent):
        self.control = self._create_control()
        self.sync_value(self.factory.refresh, "refresh", "from")
        self.update_editor()

    def _create_control(self):
        q = QWebEngineView()
        # q.resize(self.item.width, self.item.height)
        print(self.item.width, self.item.height)
        return q

    def update_editor(self):
        html = self.value.render()
        self.control.setHtml(html)

    def _refresh_fired(self):
        self.update_editor()


class WebViewEditor(BasicEditorFactory):
    """wxPython editor factory for Enable components."""

    # ---------------------------------------------------------------------------
    #  Trait definitions:
    # ---------------------------------------------------------------------------

    # The class used to create all editor styles (overrides BasicEditorFactory).
    klass = _WebViewEditor
    refresh = Str


class Center(HasTraits):
    x = Float(-116.0, enter_set=True, auto_set=False)
    y = Float(35.0, enter_set=True, auto_set=False)
    zoom = Range(1, 20, 6)

    xlabel = Str("Longitude")
    ylabel = Str("Latitude")

    @property
    def location(self):
        return [self.y, self.x]


class FoliumMap(HasTraits):
    center = Instance(Center, ())

    def __init__(self, *args, **kw):
        super(FoliumMap, self).__init__(*args, **kw)
        m = folium.Map(location=self.center.location, zoom_start=self.center.zoom)

        folium.TileLayer(tiles="OpenStreetMap").add_to(m)
        folium.TileLayer(tiles="Stamen Terrain").add_to(m)
        folium.LayerControl().add_to(m)

        self._map = m

    def render(self):
        root = self._map.get_root()
        return root.render()

    def add_marker(self, **kw):
        m = folium.Marker(**kw)
        m.add_to(self._map)


class MapFigureEditor(BaseEditor):
    fmap = Instance(FoliumMap, ())
    refresh = Event

    def load(self):
        lats, lons = [], []
        for name, ans in groupby_key(self.items, key=attrgetter("sample")):
            record = list(ans)[0]
            # samples = [(35, -116.15), (35.23, -116.34)]
            if record.latitude and record.longitude:
                lats.append(record.latitude)
                lons.append(record.longitude)
                self.fmap.add_marker(
                    location=(record.latitude, record.longitude),
                    popup="<b>{}</b>".format(record.sample),
                )
        if lats:
            self.fmap.center.x = sum(lons) / len(lons)
            self.fmap.center.y = sum(lats) / len(lats)

            self.refresh = True

    @on_trait_change("fmap.center.[x,y,zoom]")
    def center_changed(self):
        self.fmap._map.location = self.fmap.center.location
        self.refresh = True

    def traits_view(self):
        center_grp = VGroup(
            HGroup(
                UReadonly("object.fmap.center.ylabel"),
                UItem("object.fmap.center.y"),
                UReadonly("object.fmap.center.xlabel"),
                UItem("object.fmap.center.x"),
            )
        )

        ctrl_grp = VGroup(center_grp)
        v = View(
            ctrl_grp,
            Item(
                "fmap",
                editor=WebViewEditor(refresh="refresh"),
                width=1200,
                height=900,
                show_label=False,
            ),
            resizable=True,
        )
        return v


if __name__ == "__main__":
    m = MapFigureEditor()
    m.load()
    m.configure_traits()
# ============= EOF =============================================
