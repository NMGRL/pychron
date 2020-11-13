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

from PyQt5.QtCore import Qt, QVariant
from PyQt5.QtWidgets import QMessageBox, QMenu, QSplitter
from qgis.coref import QgsVectorLayer, QgsPointXY, QgsGeometry, QgsFeature, QgsProject, QgsRasterLayer, \
    QgsApplication, \
    QgsCoordinateReferenceSystem, QgsField, QgsMarkerSymbol
from qgis.gui import QgsMapCanvas, QgsLayerTreeViewMenuProvider, QgsMapToolIdentifyFeature
from traits.api import HasTraits, Instance, Str, Event, Float, Any, List, Button
from traitsui.api import View, Item, UItem, HSplit
from traitsui.qt4.basic_editor_factory import BasicEditorFactory
from traitsui.qt4.editor import Editor

from pychron.core.helpers.iterfuncs import groupby_key
from pychron.options.options_manager import IdeogramOptionsManager
from pychron.pipeline.plot.editors.base_editor import BaseEditor
from pychron.pipeline.plot.editors.ideogram_editor import IdeogramEditor
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
        m.addAction("Show Extent", self.showExtent)
        m.addAction("Position to Extent", self.position_to_extent)
        m.addAction("Toggle Visible", self.toggle_visible)
        return m

    def position_to_extent(self):
        layer = self.view.currentLayer()
        r = layer.extent()
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

    def showExtent(self):
        r = self.view.currentLayer().extent()
        QMessageBox.information(None, "Extent", r.toString())


class _QGISEditor(Editor):
    refresh = Event
    selected_feature = Any
    data_layer = Any
    rlayer = Any
    view = Any
    root = Any
    model = Any
    toolZoomIn = Any
    toolZoomOut = Any
    toolPan = Any
    toolInfo = Any
    actionZoomIn = Any
    actionZoomOut = Any
    actionPan = Any
    actionInfo = Any
    toolbar = Any
    canvas = Any

    def init(self, parent):
        self.control = self._create_control(parent)
        self.sync_value(self.factory.refresh, 'refresh', 'from')
        self.sync_value(self.factory.selected_feature, 'selected_feature', 'to')
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

        crs = QgsCoordinateReferenceSystem('EPSG:4326')
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
        layer = QgsVectorLayer(uri, "Data", "memory")
        provider = layer.dataProvider()

        provider.addAttributes([QgsField("uuid", QVariant.String)])
        layer.updateFields()

        self.data_layer = layer

        sd = getattr(self.value, 'symbol_style')
        if sd is None:
            sd = {'name': 'circle', 'size': '4', 'color': 'blue'}

        layer.renderer().setSymbol(QgsMarkerSymbol.createSimple(sd))

        qproject.addMapLayer(layer)

        args = getattr(self.value, 'basemap')
        rlayer = QgsRasterLayer(*args)
        if rlayer.isValid():
            qproject.addMapLayer(rlayer)
        else:
            print('basemap layer invalid', rlayer, args)

        # self.root = root = qproject.layerTreeRoot()
        # self.view = view = QgsLayerTreeView()
        # self.model = model = QgsLayerTreeModel(root)
        # view.setModel(model)
        # view.collapseAll()

        # provider = MyMenuProvider(canvas, root, view)
        # view.setMenuProvider(provider)

        # layout.addWidget(view)
        # layout.addWidget(canvas)

        self.toolInfo.setLayer(layer)
        canvas.setLayers([layer, rlayer])
        self.canvas = canvas

        return canvas

    def update_editor(self):

        layer = self.data_layer

        fets = []
        for f in self.value.features:
            fet = QgsFeature(layer.fields())
            fet.setAttribute('uuid', f.uuid)
            fet.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(f.x, f.y)))
            fets.append(fet)

        res, out = layer.dataProvider().addFeatures(fets)
        ext = layer.extent()
        ext.grow(0.5)

        self.canvas.setExtent(ext)
        layer.triggerRepaint()

    def _refresh_fired(self):
        self.update_editor()


class QGISEditor(BasicEditorFactory):
    klass = _QGISEditor
    refresh = Str
    selected_feature = Str


class Feature(HasTraits):
    x = Float
    y = Float
    name = Str
    uuid = Str
    analyses = List

    def traits_view(self):
        return View(Item('name'), Item('x'), Item('y'))


class QGISMap(HasTraits):
    features = List
    symbol_style = None
    uri = Str('type=xyz&url=http://tile.openstreetmap.org/{z}/{x}/{y}.png&zmax=19&zmin=5')

    @property
    def basemap(self):
        uri = self.uri
        if any(uri.endswith(e) for e in ('.png', '.tif', '.tiff', '.jpeg', '.jpg')):
            args = (uri, 'BaseMap')
        else:
            args = (uri, 'BaseMap', 'wms')

        return args


class GISFigureEditor(BaseEditor):
    qmap = Instance(QGISMap, ())
    refresh = Event
    selected_feature = Any
    refresh_button = Button
    active_feature = Instance(Feature, ())
    ideogram = Instance(IdeogramEditor, ())
    options = Any

    qgs = QgsApplication([], False)
    qgs.initQgis()

    def _selected_feature_changed(self, new):
        u = new.attribute('uuid')
        for f in self.qmap.features:
            if f.uuid == u:
                self.active_feature = f
                self.ideogram.set_items(f.analyses)
                break
        else:
            self.ideogram.set_items(self.items)

        self.ideogram.refresh_needed = True

    def load(self):

        features = []

        p = IdeogramOptionsManager()
        options = p.selected_options

        options.trait_set(padding_left=40,
                          padding_right=10,
                          padding_top=20,
                          padding_bottom=40)
        ap = options.aux_plots[1]
        ap.name = 'Ideogram'
        ap.plot_enabled = True

        ap = options.aux_plots[0]
        ap.name = 'Analysis Number'
        ap.plot_enabled = True

        self.ideogram.plotter_options = options
        self.ideogram.set_items(self.items)

        for i, (name, ans) in enumerate(groupby_key(self.items, key=attrgetter('sample'))):
            ans = list(ans)
            record = ans[0]
            for a in ans:
                a.group_id = i
            features.append(Feature(x=record.longitude,
                                    y=record.latitude,
                                    name=record.sample,
                                    uuid=str(uuid.uuid4()),
                                    analyses=ans
                                    ))

        self.qmap.uri = self.options.basemap_uri
        self.qmap.features = features
        self.qmap.symbol_style = self.options.symbol_style()
        self.refresh = True

    # def _refresh_button_fired(self):
    #     self.load()
    #     self.refresh = True
    #     self.ideogram.refresh_needed = True

    def traits_view(self):

        # center_grp = VGroup(HGroup(
        #     UReadonly('object.fmap.center.ylabel'), UItem('object.fmap.center.y'),
        #     UReadonly('object.fmap.center.xlabel'), UItem('object.fmap.center.x')))
        #
        # ctrl_grp = VGroup(center_grp)
        # UItem('active_feature', style='custom')
        v = View(
            HSplit(UItem('qmap', editor=QGISEditor(refresh='refresh',
                                                   selected_feature='selected_feature')),
                   UItem('ideogram', style='custom')
                   ),
            # width=500, height=500,
            resizable=True)
        return v


if __name__ == '__main__':
    m = GISFigureEditor()

    qgs = QgsApplication([], False)
    qgs.initQgis()
    from pychron.paths import paths

    paths.build('PychronDev')
    class Options:
        basemap_uri = 'type=xyz&url=http://tile.openstreetmap.org/{z}/{x}/{y}.png&zmax=19&zmin=5'
        basemap_uri = 'type=xyz&url=http://a.tile.stamen.com/terrain/{z}/{x}/{y}.png&zmax=19&zmin=5'
        basemap_uri = 'type=xyz&url=http://a.tile.opentopomap.org/{z}/{x}/{y}.png&zmax=19&zmin=5'
        basemap_uri = 'type=xyz&url=https://basemap.nationalmap.gov/arcgis/rest/services/USGSImageryOnly/MapServer/tile/{Z}/{Y}/{X}&zmax=19&zmin=5'
        basemap_uri = 'type=xyz&url=https://tileserver.maptiler.com/nasa/{Z}/{X}/{Y}.jpg&zmax=19&zmin=5'
        basemap_uri = 'url=https://landsatlook.usgs.gov/arcgis/services/LandsatLook/ImageServer/WMSServer'
        basemap_uri = 'type=xyz&url=http://tiles.wmflabs.org/hillshading/{z}/{x}/{y}.png&zmax=19&zmin=5'


    class MockItem(NonDBAnalysis):
        def __init__(self, sample, lat, lon, age, omit=False):
            self.latitude = lat
            self.longitude = lon
            self.sample = sample
            self.age = age
            self.age_err = 0.1
            if omit:
                self.set_tag('omit')
            super(MockItem, self).__init__()


    m.items = [
        MockItem('foo', 34, -106, 1.5),
        MockItem('foo', 34, -106, 1.3),
        MockItem('foo', 34, -106, 1.1),

        MockItem('bar', 35.1, -106.1, 21.1),
        MockItem('bar', 35.1, -106.1, 21.2),
        MockItem('bar', 35.1, -106.1, 21.4),

        MockItem('moo', 35.3, -106.5, 1.4),
        MockItem('moo', 35.3, -106.5, 1.2, omit=True),
        MockItem('moo', 35.3, -106.5, 1.5),
        MockItem('moo', 35.3, -106.5, 1.6),
    ]
    m.options = Options()
    m.load()
    m.configure_traits()
# ============= EOF =============================================
