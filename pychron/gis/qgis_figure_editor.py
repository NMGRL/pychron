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
import uuid
from operator import attrgetter

from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt, QVariant
from PyQt5.QtWidgets import QMenu, QSplitter
from qgis.core import (
    QgsVectorLayer,
    QgsPointXY,
    QgsGeometry,
    QgsFeature,
    QgsProject,
    QgsRasterLayer,
    QgsApplication,
    QgsCoordinateReferenceSystem,
    QgsField,
    QgsMarkerSymbol,
    QgsCategorizedSymbolRenderer,
    QgsRendererCategory,
    QgsLayerTreeModel,
)
from qgis.gui import (
    QgsMapCanvas,
    QgsLayerTreeViewMenuProvider,
    QgsMapToolIdentifyFeature,
    QgsLayerTreeView,
)
from traits.api import HasTraits, Instance, Str, Event, Float, Any, List, Button, Bool
from traitsui.api import View, Item, UItem, HSplit, HGroup, BasicEditorFactory
from traitsui.qt4.editor import Editor
from pychron.core.helpers.color_generators import colornames
from pychron.core.helpers.iterfuncs import groupby_key
from pychron.options.options_manager import IdeogramOptionsManager
from pychron.pipeline.plot.editors.base_editor import BaseEditor
from pychron.pipeline.plot.editors.ideogram_editor import IdeogramEditor
from pychron.processing.analyses.analysis_group import AnalysisGroup
from pychron.processing.analyses.file_analysis import NonDBAnalysis


class MyMenuProvider(QgsLayerTreeViewMenuProvider):
    def __init__(self, canvas, root, view):
        QgsLayerTreeViewMenuProvider.__init__(self)
        self.view = view
        self.root = root
        self.canvas = canvas

    def createContextMenu(self):
        if not self.view.currentLayer():
            return None

        m = QMenu()
        # m.addAction("Show Extent", self.showExtent)
        m.addAction("Position to Extent", self.position_to_extent)
        m.addAction("Toggle Visible", self.toggle_visible)
        return m

    def position_to_extent(self):
        layer = self.view.currentLayer()
        r = layer.extent()
        print(r)
        r.grow(0.5)
        layer.triggerRepaint()
        self.canvas.setExtent(r)

    def toggle_visible(self):
        layers = [lyr for lyr in self.canvas.layers()]

        for lyr in self.view.selectedLayers():
            node = self.root.findLayer(lyr.id())
            if node.isVisible():
                node.setItemVisibilityChecked(False)
                layers.remove(lyr)
            else:
                node.setItemVisibilityChecked(True)
                if isinstance(lyr, QgsRasterLayer):
                    layers.append(lyr)
                else:
                    layers.insert(0, lyr)
                lyr.triggerRepaint()

        self.canvas.setLayers(layers)

        self.canvas.refresh()


#
#     def showExtent(self):
#         r = self.view.currentLayer().extent()
#         QMessageBox.information(None, "Extent", r.toString())


class _QGISEditor(Editor):
    refresh = Event
    selected_feature = Any
    data_layer = Any
    rlayer = Any
    view = Any
    root = Any
    model = Any
    # toolZoomIn = Any
    # toolZoomOut = Any
    # toolPan = Any
    toolInfo = Any
    # actionZoomIn = Any
    # actionZoomOut = Any
    # actionPan = Any
    # actionInfo = Any
    toolbar = Any
    canvas = Any

    def init(self, parent):
        self.control = self._create_control(parent)
        self.sync_value(self.factory.refresh, "refresh", "from")
        self.sync_value(self.factory.selected_feature, "selected_feature", "to")
        self.infotool()
        # self.update_editor()

    # def zoomIn(self):
    #     self.canvas.setMapTool(self.toolZoomIn)
    #
    # def zoomOut(self):
    #     self.canvas.setMapTool(self.toolZoomOut)
    #
    # def pan(self):
    #     self.control.setMapTool(self.toolPan)

    def infotool(self):
        self.canvas.setMapTool(self.toolInfo)

    def feature_identified(self, feature):
        self.selected_feature = feature

    def _create_control(self, parent):
        layout = QSplitter()
        layout.setOrientation(Qt.Horizontal)

        canvas = QgsMapCanvas()

        crs = QgsCoordinateReferenceSystem(self.value.crs)
        canvas.setDestinationCrs(crs)

        canvas.setCanvasColor(Qt.white)
        canvas.enableAntiAliasing(True)

        # self.toolbar = self.ui.owner.control._mw.addToolBar("Canvas actions")

        # self.actionZoomIn = QAction("Zoom in")
        # self.actionZoomOut = QAction("Zoom out")
        # self.actionPan = QAction("Pan")
        # self.actionInfo = QAction('Info')
        #
        # self.toolbar.addAction(self.actionZoomIn)
        # self.toolbar.addAction(self.actionZoomOut)
        # self.toolbar.addAction(self.actionPan)
        # self.toolbar.addAction(self.actionInfo)

        # self.actionZoomIn.setCheckable(True)
        # self.actionZoomOut.setCheckable(True)
        # self.actionPan.setCheckable(True)
        # self.actionInfo.setCheckable(True)

        # self.actionZoomIn.triggered.connect(self.zoomIn)
        # self.actionZoomOut.triggered.connect(self.zoomOut)
        # self.actionPan.triggered.connect(self.pan)
        # self.actionInfo.triggered.connect(self.infotool)

        # self.toolPan = QgsMapToolPan(canvas)
        # self.toolPan.setAction(self.actionPan)
        # self.toolZoomIn = QgsMapToolZoom(canvas, False)  # false = in
        # self.toolZoomIn.setAction(self.actionZoomIn)
        # self.toolZoomOut = QgsMapToolZoom(canvas, True)  # true = out
        # self.toolZoomOut.setAction(self.actionZoomOut)

        self.toolInfo = QgsMapToolIdentifyFeature(canvas)  # true = out
        # self.toolInfo.setAction(self.actionInfo)
        self.toolInfo.featureIdentified.connect(self.feature_identified)

        qproject = QgsProject.instance()
        uri = "Point?crs=epsg:4326&field=id:integer"
        self.data_layer = layer = QgsVectorLayer(uri, "Data", "memory")
        provider = layer.dataProvider()

        provider.addAttributes(
            [QgsField("uuid", QVariant.String), QgsField("group_id", QVariant.Int)]
        )
        layer.updateFields()

        self.set_symbol()

        # args = getattr(self.value, 'basemap')
        self.rlayer = rlayer = QgsRasterLayer(*self.value.basemap)
        if rlayer.isValid():
            qproject.addMapLayer(rlayer)
        else:
            print("basemap layer invalid", rlayer, self.value.basemap)

        qproject.addMapLayer(layer)
        canvas.setLayers([layer, rlayer])

        self.root = root = qproject.layerTreeRoot()
        self.view = view = QgsLayerTreeView()
        self.model = model = QgsLayerTreeModel(root)

        view.setModel(model)
        view.collapseAll()

        provider = MyMenuProvider(canvas, root, view)
        view.setMenuProvider(provider)

        layout.addWidget(view)
        view.setMaximumWidth(200)
        layout.addWidget(canvas)
        layout.setSizePolicy(
            QtWidgets.QSizePolicy(
                QtWidgets.QSizePolicy.MinimumExpanding,
                QtWidgets.QSizePolicy.MinimumExpanding,
            )
        )

        self.toolInfo.setLayer(layer)
        self.canvas = canvas

        return layout

    def set_symbol(self, layer=None, options=None):
        if layer is None:
            layer = self.data_layer

        if options is None:
            options = [{"name": "circle", "size": "4", "color": "blue"}]

        renderer = QgsCategorizedSymbolRenderer(attrName="group_id")
        for i, option in enumerate(options):
            symbol = QgsMarkerSymbol.createSimple(option)
            symbol.setOpacity(float(option.get("opacity", 1)))
            cat = QgsRendererCategory(str(i), symbol, "")
            renderer.addCategory(cat)
        layer.setRenderer(renderer)

    def update_editor(self):
        layers = [self.data_layer, self.rlayer]
        project = QgsProject.instance()

        self.rlayer.dataProvider().setDataSourceUri(self.value.uri)
        mext = None
        for loption in self.value.layers:
            if loption.is_vector:
                for key in project.mapLayers():
                    el = project.mapLayer(key)
                    if el.dataProvider().dataSourceUri() == loption.uri:
                        project.removeMapLayer(key)
                        break

                layer = QgsVectorLayer(loption.uri, loption.label, loption.provider)

            else:
                layer = QgsRasterLayer(loption.uri, loption.label)

            if layer.isValid():
                layer.renderer().setSymbol(
                    QgsMarkerSymbol.createSimple(loption.symbolargs)
                )

                # make sure to add layer after setting renderer
                # probably a way to sync the tree view with the renderer but by
                # setting the renderer before adding the tree view is up to date
                project.addMapLayer(layer)

                ext = layer.extent()

                ext.grow(1.75)
                if mext is None:
                    mext = ext
                else:
                    mext.combineExtentWith(ext)
            else:
                print("not valid", layer, loption.uri)

            if loption.visible:
                layers.insert(0, layer)

        dlayer = self.data_layer
        fgs, options = zip(*self.value.feature_groups)

        self.set_symbol(options=options)
        provider = dlayer.dataProvider()
        provider.truncate()

        fets = []

        for i, fs in enumerate(fgs):
            for f in fs:
                fet = QgsFeature(dlayer.fields())
                fet.setAttribute("uuid", f.uuid)
                fet.setAttribute("group_id", i)
                fet.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(f.x, f.y)))
                fets.append(fet)

        provider.addFeatures(fets)
        dext = dlayer.extent()
        dext.grow(0.5)
        if mext is not None:
            dext.combineExtentWith(mext)

        self.canvas.setLayers(layers)
        self.canvas.setExtent(dext)

    def _refresh_fired(self):
        self.update_editor()


class QGISEditor(BasicEditorFactory):
    klass = _QGISEditor
    refresh = Str
    selected_feature = Str
    tree_enabled = Bool(True)


class Feature(HasTraits):
    x = Float
    y = Float
    name = Str
    uuid = Str
    analysis_group = Instance(AnalysisGroup, ())

    def traits_view(self):
        return View(
            HGroup(Item("x"), Item("y")),
            Item("object.analysis_group.sample"),
            Item("object.analysis_group.weighted_age"),
            Item("object.analysis_group.mswd"),
            Item("object.analysis_group.age_span"),
        )


class QGISMap(HasTraits):
    feature_groups = List
    layers = List
    uri = Str(
        "type=xyz&url=http://tile.openstreetmap.org/{z}/{x}/{y}.png&zmax=19&zmin=5"
    )
    crs = Str("EPSG:4326")

    @property
    def basemap(self):
        uri = self.uri
        if any(uri.endswith(e) for e in (".png", ".tif", ".tiff", ".jpeg", ".jpg")):
            args = (uri, "BaseMap")
        else:
            args = (uri, "BaseMap", "wms")

        return args


class GISFigureEditor(BaseEditor):
    qmap = Instance(QGISMap, ())
    refresh = Event
    selected_feature = Any
    active_feature = Instance(Feature, ())
    ideogram = Instance(IdeogramEditor, ())
    plotter_options = Any
    refresh_button = Button
    qgs = QgsApplication([], False)
    qgs.initQgis()

    def refresh_map(self):
        self._load_qmap()

    def _selected_feature_changed(self, new):
        u = new.attribute("uuid")

        fs = (fi for fs, _ in self.qmap.feature_groups for fi in fs)
        for f in fs:
            if f.uuid == u:
                self.active_feature = f
                self.ideogram.set_items(f.analysis_group.analyses)
                break
        else:
            self.ideogram.set_items(self.items)

        self.ideogram.refresh_needed = True

    def load(self):

        p = IdeogramOptionsManager()
        options = p.selected_options

        options.trait_set(
            padding_left=40,
            padding_right=10,
            padding_top=20,
            padding_bottom=40,
            include_group_legend=False,
        )
        ap = options.aux_plots[1]
        ap.name = "Ideogram"
        ap.plot_enabled = True

        ap = options.aux_plots[0]
        ap.name = "Analysis Number"
        ap.plot_enabled = True
        ap.x_error = True

        self.ideogram.plotter_options = options

        self.ideogram.set_items(self.items)

        # force generation of component
        self.ideogram.component

        self._load_qmap()

    def _load_qmap(self):
        ags = []
        # get the groups from the ideogram
        for p in self.ideogram.figure_model.panels:
            ags.extend([pp.analysis_group for pp in p.figures])

        # then group the groups by their feature_group_ids
        # feature_group_id set by SampleGroupingNode
        feature_groups = []
        po = self.plotter_options
        for i, (feature_group, agis) in enumerate(
            groupby_key(ags, key=attrgetter("featuregroup_id"))
        ):
            features = [
                Feature(
                    x=ag.longitude,
                    y=ag.latitude,
                    uuid=str(uuid.uuid4()),
                    analysis_group=ag,
                )
                for ag in agis
            ]

            feature_options = po.get_feature_options(i)
            feature_groups.append((features, feature_options))

        self.qmap.uri = self.plotter_options.basemap_uri
        self.qmap.feature_groups = feature_groups
        self.qmap.layers = self.plotter_options.layers

        self.refresh = True

    def _refresh_button_fired(self):
        # self.plotter_options.symbol_kind = 'square'
        self.refresh_map()

    def traits_view(self):

        # center_grp = VGroup(HGroup(
        #     UReadonly('object.fmap.center.ylabel'), UItem('object.fmap.center.y'),
        #     UReadonly('object.fmap.center.xlabel'), UItem('object.fmap.center.x')))
        #
        # ctrl_grp = VGroup(center_grp)
        v = View(
            UItem("active_feature", style="custom"),
            UItem("refresh_button"),
            HSplit(
                UItem(
                    "qmap",
                    editor=QGISEditor(
                        refresh="refresh", selected_feature="selected_feature"
                    ),
                ),
                UItem("ideogram", style="custom"),
            ),
            # width=500, height=500,
            resizable=True,
        )
        return v


if __name__ == "__main__":
    m = GISFigureEditor()

    qgs = QgsApplication([], False)
    qgs.initQgis()
    from pychron.paths import paths

    paths.build("PychronDev")

    class Options:
        basemap_uri = (
            "type=xyz&url=http://tile.openstreetmap.org/{z}/{x}/{y}.png&zmax=19&zmin=5"
        )
        # basemap_uri = 'type=xyz&url=http://a.tile.stamen.com/terrain/{z}/{x}/{y}.png&zmax=19&zmin=5'
        # basemap_uri = 'type=xyz&url=http://a.tile.opentopomap.org/{z}/{x}/{y}.png&zmax=19&zmin=5'
        # basemap_uri = 'type=xyz&url=https://basemap.nationalmap.gov/arcgis/rest/services/' \
        #               'USGSImageryOnly/MapServer/tile/{Z}/{Y}/{X}&zmax=19&zmin=5'
        # basemap_uri = 'type=xyz&url=https://tileserver.maptiler.com/nasa/{Z}/{X}/{Y}.jpg&zmax=19&zmin=5'
        # basemap_uri = 'url=https://landsatlook.usgs.gov/arcgis/services/LandsatLook/ImageServer/WMSServer'
        # basemap_uri = 'type=xyz&url=http://tiles.wmflabs.org/hillshading/{z}/{x}/{y}.png&zmax=19&zmin=5'
        layers = []
        symbol_kind = "circle"

        # def symbol_style(self):
        #     return {'name': self.symbol_kind, 'size': '4'}
        def get_feature_options(self, i):
            return {
                "name": "pentagon",
                "size": "10",
                "angle": "25",
                "opacity": ".25",
                "color": colornames[i + 2],
            }

    class MockItem(NonDBAnalysis):
        def __init__(self, sample, gid, mid, lat, lon, age, omit=False):
            self.latitude = lat
            self.longitude = lon
            self.sample = sample
            self.age = age
            self.age_err = 0.1
            self.group_id = gid
            self.featuregroup_id = mid

            if omit:
                self.set_tag("omit")
            super(MockItem, self).__init__()

    m.items = [
        MockItem("foo", 0, 0, 34, -106, 1.5),
        MockItem("foo", 0, 0, 34, -106, 1.3),
        MockItem("foo", 0, 0, 34, -106, 1.1),
        MockItem("bar", 1, 0, 35.1, -106.1, 21.1),
        MockItem("bar", 1, 0, 35.1, -106.1, 21.2),
        MockItem("bar", 1, 0, 35.1, -106.1, 21.4),
        MockItem("moo", 2, 1, 35.3, -106.5, 1.4),
        MockItem("moo", 2, 1, 35.3, -106.5, 1.2, omit=True),
        MockItem("moo", 2, 1, 35.3, -106.5, 1.5),
        MockItem("moo", 2, 1, 35.3, -106.5, 1.6),
    ]
    m.plotter_options = Options()
    m.load()
    m.configure_traits()
# ============= EOF =============================================
