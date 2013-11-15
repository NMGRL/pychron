#!/Library/Frameworks/Python.framework/Versions/Current/bin/python
#===============================================================================
# Copyright 2012 Jake Ross
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
#===============================================================================

#============= enthought library imports =======================

from traitsui.api import View, Item, Group, VGroup, HGroup, ListEditor, InstanceEditor
from traits.api import Int, Button, Str, on_trait_change, Bool, Color, List
from chaco.api import HPlotContainer, ArrayPlotData, Plot
from chaco.tools.api import ZoomTool
from chaco.default_colormaps import color_map_name_dict
from enable.component import Component
#============= standard library imports ========================
import sys
import os
# from PIL import Image
from numpy import sum, zeros_like, where, array, percentile, hsplit
# from pychron.image.processing.bandwidth_highlighter import BandwidthHighlighter
#============= local library imports  ==========================
#============= enthought library imports =======================

#============= standard library imports ========================
from PIL import Image
#============= local library imports  ==========================
from chaco.tools.image_inspector_tool import ImageInspectorTool, \
    ImageInspectorOverlay
from enable.component_editor import ComponentEditor

from chaco.tools.pan_tool import PanTool


class Band(HasTraits):
    center = Int(enter_set=True, auto_set=False)
    threshold = Int(enter_set=True, auto_set=False)
    color = Color
    use = Bool(False)
    def traits_view(self):
        v = View(HGroup(Item('use', show_label=False,), Item('center'), Item('threshold'), Item('color', style='custom', show_label=False)))
        return v

class BandwidthHighlighter(HasTraits):

    container = Instance(HPlotContainer)
    plot = Instance(Component)

    colormap_name_1 = Str('gray')

    path = Str
    add_band = Button('Add band')
    highlight_bands = List(Band)
    def update_path(self, new):
        self.path = new

    def _add_band_fired(self):
        self.highlight_bands.append(Band())

    def _path_changed(self):
        self._load_image(self.path)

    @on_trait_change('highlight_bands:[center,threshold,color, use]')
    def _refresh_highlight_bands(self, obj, name, old, new):
        if self.path:
            plot = self.oplot
            im = Image.open(self.path)
            rgb_arr = array(im.convert('RGB'))
#            im_arr=array(im)
            gray_im = array(im.convert('L'))
            for band in self.highlight_bands:
                if band.use:
                    low = band.center - band.threshold
                    high = band.center + band.threshold

                    mask = where((gray_im > low) & (gray_im < high))
#                    print band.color[:3]
                    rgb_arr[mask] = band.color[:3]

            imgplot = plot.plots['plot0'][0]
            tools = imgplot.tools
            overlays = imgplot.overlays

            plot.delplot('plot0')
            plot.data.set_data('img', rgb_arr)
            img_plot = plot.img_plot('img', colormap=color_map_name_dict[self.colormap_name_1])[0]

            for ti in tools + overlays:
                ti.component = img_plot

            img_plot.tools = tools
            img_plot.overlays = overlays

            plot.request_redraw()

#
    def _load_image(self, path):
        self.container = self._container_factory()
        im = Image.open(path)
#        oim = array(im)
        im = im.convert('L')
        odim = ndim = array(im)

        pd = ArrayPlotData()
        pd.set_data('img', odim)
        plot = Plot(data=pd, padding=[30, 5, 5, 30], default_origin='top left')
        img_plot = plot.img_plot('img',
                                 colormap=color_map_name_dict[self.colormap_name_1]
                                 )[0]
        self.add_inspector(img_plot)

        self.add_tools(img_plot)

        self.oplot = plot

        self.container.add(self.oplot)
#        self.container.add(self.plot)
        self.container.request_redraw()

    def add_inspector(self, img_plot):
        imgtool = ImageInspectorTool(img_plot)
        img_plot.tools.append(imgtool)
        overlay = ImageInspectorOverlay(component=img_plot, image_inspector=imgtool,
                                        bgcolor="white", border_visible=True)

        img_plot.overlays.append(overlay)
#
    def add_tools(self, img_plot):
        zoom = ZoomTool(component=img_plot, tool_mode="box", always_on=False)
        pan = PanTool(component=img_plot, restrict_to_data=True)
        img_plot.tools.append(pan)

        img_plot.overlays.append(zoom)

    def _highlight_bands_default(self):
        return [Band(color='red'), Band(color='green'), Band(color='blue')]

    def traits_view(self):
        ctrl_grp = VGroup(
                        HGroup(Item('add_band', show_label=False)),
                        Item('highlight_bands', editor=ListEditor(mutable=False,
                                                                 style='custom', editor=InstanceEditor()))
                        )
        v = View(
               ctrl_grp,
               Item('container', show_label=False,
                       editor=ComponentEditor()),
#
#                 title='Color Inspector',
                 resizable=True,
                 height=800,
                 width=900
                 )
        return v

    def _container_factory(self):
        pc = HPlotContainer(padding=[5, 5, 5, 20])
        return pc

    def _container_default(self):
        return self._container_factory()


class ImageProcessor(HasTraits):
    path = File

    highlighter = Instance(BandwidthHighlighter)
    def traits_view(self):
        main_grp = Group(Item('path'))
        highlight_bands_grp = Item('highlighter', show_label=False, style='custom')
        v = View(
               VGroup(main_grp,
                      Group(highlight_bands_grp,
                            layout='tabbed'
                            )
                     ),
               resizable=True,
               width=800,
               height=900
               )
        return v

    def _highlighter_default(self):
        h = BandwidthHighlighter(path=self.path)
        self.on_trait_change(h.update_path, 'path')
        return h

if __name__ == '__main__':
    d = ImageProcessor()
    if len(sys.argv) > 1:
        path = os.path.join(os.getcwd(), sys.argv[1])
        d.path = path

    # d.path='/Users/argonlab2/Sandbox/R2-03 closeup_1_BSE_1 zoomed2.png'
    d.configure_traits()
#============= EOF =============================================
