#!/Library/Frameworks/Python.framework/Versions/Current/bin/python
# ===============================================================================
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
# ===============================================================================

# ============= enthought library imports =======================
from chaco.api import HPlotContainer, ArrayPlotData, Plot
from chaco.default_colormaps import color_map_name_dict
from chaco.tools.api import ZoomTool
from enable.component import Component
from pyface.constant import OK
from pyface.file_dialog import FileDialog
from traits.api import HasTraits, Int, Enum, File, Instance, Button, Float, Str, on_trait_change, Bool, Color, List
from traitsui.api import View, Item, VGroup, HGroup, ListEditor, InstanceEditor

# ============= standard library imports ========================
from PIL import Image
from numpy import sum, zeros_like, where, array
# ============= local library imports  ==========================
from chaco.tools.image_inspector_tool import ImageInspectorTool, \
    ImageInspectorOverlay
from enable.component_editor import ComponentEditor
import os
import sys
from chaco.tools.pan_tool import PanTool
class Band(HasTraits):
    center = Int(enter_set=True, auto_set=False)
    threshold = Int(enter_set=True, auto_set=False)
    color = Color
    use = Bool(False)
    def traits_view(self):
        v = View(HGroup(Item('use', show_label=False,), Item('center'), Item('threshold'), Item('color', style='custom', show_label=False)))
        return v

class BandwidthImager(HasTraits):
    use_threshold = Bool(False)
    low = Int(120, enter_set=True, auto_set=False)
    high = Int(150, enter_set=True, auto_set=False)
    contrast_low = Int(2, enter_set=True, auto_set=False)
    contrast_high = Int(98, enter_set=True, auto_set=False)
    histogram_equalize = Bool(False)
    container = Instance(HPlotContainer)
    plot = Instance(Component)
    oplot = Instance(Component)
    highlight = Int(enter_set=True, auto_set=False)
    highlight_threshold = Int(enter_set=True, auto_set=False)

    area = Float
    colormap_name_1 = Str('gray')
    colormap_name_2 = Str('gray')
    save_button = Button('Save')
    save_mode = Enum('both', 'orig', 'thresh')
    path = File
#    save_both = Bool
#    save_orig = Bool
#    save_thresh = Bool

#    calc_area_button = Button
    calc_area_value = Int(auto_set=False, enter_set=True)
    calc_area_threshold = Int(4, auto_set=False, enter_set=True)
    contrast_equalize = Bool(False)

    highlight_bands = List(Band)

    @on_trait_change('highlight+')
    def _highlight_changed(self):
        im = Image.open(self.path)
        ndim = array(im.convert('L'))
        im = array(im.convert('RGB'))

        low = self.highlight - self.highlight_threshold
        high = self.highlight + self.highlight_threshold
        mask = where((ndim > low) & (ndim < high))

        im[mask] = [255, 0, 0]
#        im = Image.fromarray(im)

        plot = self.oplot

        imgplot = plot.plots['plot0'][0]
        tools = imgplot.tools
        overlays = imgplot.overlays

        plot.delplot('plot0')
        plot.data.set_data('img', im)
        img_plot = plot.img_plot('img')[0]

        for ti in tools:
            ti.component = img_plot
        for oi in overlays:
            oi.component = img_plot

        img_plot.tools = tools
        img_plot.overlays = overlays
        plot.request_redraw()

#    def _histogram_equalize_changed(self):
#        if not (self.oplot and self.plot):
#            return
#        if self.histogram_equalize:
#            plot = self.plot
#            pychron = self._ndim
#            self._hdim = hdim = equalize(pychron) * 255
#            plot.data.set_data('img', hdim)
#            plot.request_redraw()
#
#        elif self.path:
#            self._load_image(self.path)
#
#        self.container.request_redraw()

#    @on_trait_change('contrast+')
#    def _contrast_changed(self):
# #        if self.path:
# #            self._load_image(self.path)
#        if not (self.oplot and self.plot):
#            return
#
#        if self.contrast_equalize:
#            plot = self.plot
#            pychron = self._ndim
#            img_rescale = self._contrast_equalize(pychron)
#            plot.data.set_data('img', img_rescale)
#            plot.request_redraw()
#
#        else:
#            if self.path:
#                self._load_image(self.path)
# #                img_rescale = self._ndim
# #
#
#    def _contrast_equalize(self, pychron):
#        p2 = percentile(pychron, self.contrast_low)
#        p98 = percentile(pychron, self.contrast_high)
#        img_rescale = rescale_intensity(pychron,
#                                        in_range=(p2, p98)
#                                        )
#        return img_rescale

    def _path_changed(self):
        self._load_image(self.path)

    @on_trait_change('highlight_bands:[center,threshold,color]')
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

            plot.delplot('plot0')
            plot.data.set_data('img', rgb_arr)
            img_plot = plot.img_plot('img', colormap=color_map_name_dict[self.colormap_name_1])[0]
            plot.request_redraw()

    @on_trait_change('calc_area+')
    def _calc_area(self):
        self.trait_set(low=self.calc_area_value - self.calc_area_threshold,
                       high=self.calc_area_value + self.calc_area_threshold,
                       trait_change_notify=False)
        self._refresh()

    def _save_button_fired(self):
        dlg = FileDialog(action='save as')
        if dlg.open() == OK:
            path = dlg.path
            if self.save_mode == 'orig':
                p = self.oplot
            elif self.save_mode == 'thresh':
                p = self.plot
            else:
                p = self.container

            self.render_pdf(p, path)

    def render_pdf(self, obj, path):
        from chaco.pdf_graphics_context import PdfPlotGraphicsContext

        if not path.endswith('.pdf'):
            path += '.pdf'
        gc = PdfPlotGraphicsContext(filename=path)
#        opad = obj.padding_bottom
#        obj.padding_bottom = 60
        obj.do_layout(force=True)
        gc.render_component(obj, valign='center')

        gc.gc.drawString(600, 5, 'area:{:0.3f}% low={} high={}'.format(self.area, self.low, self.high))

        gc.save()
#        obj.padding_bottom = opad

    def render_pic(self, obj, path):
        from chaco.plot_graphics_context import PlotGraphicsContext

        gc = PlotGraphicsContext((int(obj.outer_width), int(obj.outer_height)))
#            obj.use_backbuffer = False
        gc.render_component(obj)
#            obj.use_backbuffer = True
        if not path.endswith('.png'):
            path += '.png'
        gc.save(path)

    def _load_image(self, path):
        self.container = self._container_factory()
        im = Image.open(path)
#        oim = array(im)
        im = im.convert('L')
        odim = ndim = array(im)
#        if self.contrast_equalize:
#            ndim = self._contrast_equalize(ndim)

#        self._ndim = ndim
#        low = self.low
#        high = self.high
#        if self.use_threshold:
#            tim = zeros_like(ndim)
#            tim[where((ndim > low) & (ndim < high))] = 255
#            self.area = (sum(tim) / (ndim.shape[0] * ndim.shape[1])) / 255.
#        else:
#            tim = ndim

        pd = ArrayPlotData()
        pd.set_data('img', odim)
        plot = Plot(data=pd, padding=[30, 5, 5, 30], default_origin='top left')
        img_plot = plot.img_plot('img',
                                 colormap=color_map_name_dict[self.colormap_name_1]
                                 )[0]
        self.add_inspector(img_plot)

        self.add_tools(img_plot)

        self.oplot = plot

#        pd = ArrayPlotData()
#        pd.set_data('img', tim)
#        plot = Plot(data=pd,
#                    padding=[30, 5, 5, 30], default_origin='top left')
#        img_plot = plot.img_plot('img', colormap=color_map_name_dict[self.colormap_name_2])[0]
#        self.add_inspector(img_plot)
#        self.plot = plot
#
#        self.plot.range2d = self.oplot.range2d

        self.container.add(self.oplot)
#        self.container.add(self.plot)
        self.container.request_redraw()

    def add_inspector(self, img_plot):
        imgtool = ImageInspectorTool(img_plot)
        img_plot.tools.append(imgtool)
        overlay = ImageInspectorOverlay(component=img_plot, image_inspector=imgtool,
                                        bgcolor="white", border_visible=True)

        img_plot.overlays.append(overlay)

    def add_tools(self, img_plot):
        zoom = ZoomTool(component=img_plot, tool_mode="box", always_on=False)
        pan = PanTool(component=img_plot, restrict_to_data=True)
        img_plot.tools.append(pan)

        img_plot.overlays.append(zoom)

    @on_trait_change('low,high, use_threshold')
    def _refresh(self):
        if self.use_threshold:
            pd = self.plot.data

            low = self.low
            high = self.high
            if self.histogram_equalize:
                ndim = self._hdim
            else:
                ndim = self._ndim

            tim = zeros_like(ndim)
            mask = where((ndim > low) & (ndim < high))
            tim[mask] = 255

            self.area = (sum(tim) / (ndim.shape[0] * ndim.shape[1])) / 255.

            pd.set_data('img', tim)
            self.plot.request_redraw()

    def _colormap_name_1_changed(self):
        cmap = color_map_name_dict[self.colormap_name_1]
        plot = self.oplot.plots['plot0'][0]
        tools = plot.tools
        overlays = plot.overlays

        self.oplot.delplot('plot0')

        im = Image.open(self.path)
        ndim = array(im.convert('L'))
        self.oplot.data.set_data('img', ndim)
        img_plot = self.oplot.img_plot('img', colormap=cmap)[0]

        for ti in tools:
            ti.component = img_plot
        for oi in overlays:
            oi.component = img_plot

        img_plot.tools = tools
        img_plot.overlays = overlays
#        self.add_inspector(img_plot)
#        self.add_tools(img_plot)

        self.oplot.request_redraw()

    def _colormap_name_2_changed(self):
        cmap = color_map_name_dict[self.colormap_name_2]
#        self.plot.colormap = cmp
        self.plot.delplot('plot0')
        img_plot = self.plot.img_plot('img', colormap=cmap)[0]
        self.add_inspector(img_plot)
        self.plot.request_redraw()

    def _highlight_bands_default(self):
        return [Band(color='red'), Band(color='green'), Band(color='blue')]

    def traits_view(self):
        ctrl_grp = VGroup(Item('path', show_label=False),
                        Item('highlight_bands', editor=ListEditor(mutable=False,
                                                                 style='custom', editor=InstanceEditor()))
                        )
        v = View(
               ctrl_grp,
               Item('container', show_label=False,
                       editor=ComponentEditor()),
#
                 title='Color Inspector',
                 resizable=True,
                 height=800,
                 width=900
                 )
        return v
#    def traits_view(self):
#        lgrp = VGroup(Item('low'),
#                      Item('low', show_label=False, editor=RangeEditor(mode='slider', low=0, high_name='high')))
#        hgrp = VGroup(Item('high'),
#                      Item('high', show_label=False, editor=RangeEditor(mode='slider', low_name='low', high=255)))
#        savegrp = HGroup(Item('save_button', show_label=False),
#                         Item('save_mode', show_label=False))
#        ctrlgrp = VGroup(
#                         Item('path', show_label=False),
#                         HGroup(Item('use_threshold'), Item('contrast_equalize'),
#                                HGroup(Item('contrast_low'), Item('contrast_high'), enabled_when='contrast_equalize'),
#                                Item('histogram_equalize')
#                                ),
#                         HGroup(Item('highlight'), Item('highlight_threshold')),
#                         HGroup(spring,
#                                lgrp,
#                                hgrp,
#                                VGroup(savegrp,
#                                       Item('calc_area_value', label='Calc. Area For.',
#                                                     tooltip='Calculate %area for all pixels with this value'
#                                                     ),
#                                       Item('calc_area_threshold', label='Threshold +/- px',
#                                            tooltip='bandwidth= calc_value-threshold to calc_value+threshold'
#                                            )
#
#                                       )
#                                ),
#                         HGroup(spring, Item('area', style='readonly', width= -200)),
#                         HGroup(
#                                Item('colormap_name_1', show_label=False,
#                                      editor=EnumEditor(values=color_map_name_dict.keys())),
#                                spring,
#                                Item('colormap_name_2', show_label=False,
#                                     editor=EnumEditor(values=color_map_name_dict.keys()))),
#                       )
#        v = View(ctrlgrp,
#                 Item('container', show_label=False,
#                       editor=ComponentEditor()),
#
#                 title='Color Inspector',
#                 resizable=True,
#                 height=800,
#                 width=900
#
#                 )
        return v
    def _container_factory(self):
        pc = HPlotContainer(padding=[5, 5, 5, 20])
        return pc

    def _container_default(self):
        return self._container_factory()



if __name__ == '__main__':
    d = BandwidthImager()
    if len(sys.argv) > 1:
        path = os.path.join(os.getcwd(), sys.argv[1])
        d.path = path

    d.path = '/Users/argonlab2/Sandbox/R2-03 closeup_1_BSE_1 zoomed2.png'
    d.configure_traits()
# ============= EOF =============================================
