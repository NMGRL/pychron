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
from pychron.core.ui import set_qt

set_qt()

# ============= enthought library imports =======================
from chaco.abstract_overlay import AbstractOverlay
from enable.base import str_to_font
from traits.api import HasTraits, Instance, Any, Float, File, Property, Str
from traitsui.api import View, Controller, UItem, Item
from chaco.api import OverlayPlotContainer
from enable.component_editor import ComponentEditor
from pyface.api import FileDialog, OK
# ============= standard library imports ========================
from lxml.etree import ElementTree, Element
from chaco.plot import Plot
from chaco.array_plot_data import ArrayPlotData
from numpy import linspace, cos, sin, pi
import os
import csv
from chaco.data_label import DataLabel
from pychron.paths import paths
from chaco.plot_graphics_context import PlotGraphicsContext
from traitsui.menu import Action
import math
from pychron.core.helpers.filetools import to_bool
# ============= local library imports  ==========================
class myDataLabel(DataLabel):
    label_position = Any
    show_label_coords = False
    marker_visible = False
    label_position = 'center'
    border_visible = False


class LabelsOverlay(AbstractOverlay):
    def overlay(self, other_component, gc, view_bounds=None, mode="normal"):
        with gc:
            gc.set_font(str_to_font(None, None, '8'))
            for x, y, l in self.labels:
                x, y = other_component.map_screen([(x, y)])[0]
                gc.set_text_position(x - 5, y - 5)
                gc.show_text(l)


class RotatingContainer(OverlayPlotContainer):
    rotation = Float(0)

    def _draw(self, gc, *args, **kw):
        with gc:
            w2 = self.width / 2
            h2 = self.height / 2
            # gc.translate_ctm(w2, h2)
            # gc.rotate_ctm(math.radians(self.rotation))
            # gc.translate_ctm(-w2, -h2)
            super(RotatingContainer, self)._draw(gc, *args, **kw)


class GraphicGeneratorController(Controller):
    def save(self, info):
        self.model.save()

    def traits_view(self):
        w, h = 750, 750
        v = View(
            UItem('srcpath'),
            Item('rotation'),
            UItem('container', editor=ComponentEditor(), style='custom'),
            width=w + 2,
            height=h + 56,
            resizable=True,
            buttons=[Action(name='Save', action='save'), 'OK', 'Cancel'])
        return v


class GraphicModel(HasTraits):
    srcpath = File
    xmlpath = File
    container = Instance(OverlayPlotContainer)
    name = Property
    _name = Str
    rotation = Float(enter_set=True, auto_set=False)
    initialized = False

    def _get_name(self):
        return os.path.splitext(self._name if self._name else os.path.basename(self.srcpath))[0]

    def save(self, path=None):
        #        print self.container.bounds

        if path is None:
            dlg = FileDialog(action='save as', default_directory=paths.data_dir)
            if dlg.open() == OK:
                path = dlg.path

        if path is not None:
            _, tail = os.path.splitext(path)
            c = self.container
            if tail == '.pdf':
                from chaco.pdf_graphics_context import PdfPlotGraphicsContext

                gc = PdfPlotGraphicsContext(filename=path,
                                            pagesize='letter')

            else:
                if not tail in ('.png', '.jpg', '.tiff'):
                    path = '{}.png'.format(path)

                gc = PlotGraphicsContext((int(c.outer_width), int(c.outer_height)))
                #            c.use_backbuffer = False

            # for ci in c.components:
            #     try:
            #         ci.x_axis.visible = False
            #         ci.y_axis.visible = False
            #     except Exception:
            #         pass

            # c.use_backbuffer = False

            gc.render_component(c)
            #            c.use_backbuffer = True
            gc.save(path)
            self._name = os.path.basename(path)

    def load(self, path):
        parser = ElementTree(file=open(path, 'r'))
        circles = parser.find('circles')
        outline = parser.find('outline')

        bb = outline.find('bounding_box')
        bs = bb.find('width'), bb.find('height')
        w, h = map(lambda b: float(b.text), bs)

        use_label = parser.find('use_label')
        if use_label is not None:
            use_label = to_bool(use_label.text.strip())
        else:
            use_label = True

        data = ArrayPlotData()
        p = Plot(data=data, padding=100)
        p.x_grid.visible = False
        p.y_grid.visible = False

        p.x_axis.visible = False
        p.y_axis.visible = False

        p.x_axis.title = 'X cm'
        p.y_axis.title = 'Y cm'

        # font = 'modern 22'
        # p.x_axis.title_font = font
        # p.x_axis.tick_label_font = font
        # p.y_axis.title_font = font
        # p.y_axis.tick_label_font = font
        #         p.x_axis_visible = False
        #         p.y_axis_visible = False
        p.index_range.low_setting = -w / 2
        p.index_range.high_setting = w / 2

        p.value_range.low_setting = -h / 2
        p.value_range.high_setting = h / 2

        thetas = linspace(0, 2 * pi)

        radius = circles.find('radius').text
        radius = float(radius)

        face_color = circles.find('face_color')
        if face_color is not None:
            face_color = face_color.text
        else:
            face_color = 'white'
        labels = []
        for i, pp in enumerate(circles.findall('point')):
            x, y, l = pp.find('x').text, pp.find('y').text, pp.find('label').text

            #             print i, pp, x, y
            # load hole specific attrs
            r = pp.find('radius')
            if r is None:
                r = radius
            else:
                r = float(r.text)

            fc = pp.find('face_color')
            if fc is None:
                fc = face_color
            else:
                fc = fc.text

            x, y = map(float, (x, y))
            xs = x + r * sin(thetas)
            ys = y + r * cos(thetas)

            xn, yn = 'px{:03d}'.format(i), 'py{:03d}'.format(i)
            data.set_data(xn, xs)
            data.set_data(yn, ys)

            plot = p.plot((xn, yn),
                          face_color=fc,
                          type='polygon')[0]
            labels.append((x, y, l))
            # if use_label:
            #     label = myDataLabel(component=plot,
            #                         data_point=(x, y),
            #                         label_text=l,
            #                         bgcolor='transparent')
            #     plot.overlays.append(label)
        if use_label:
            p.overlays.append(LabelsOverlay(component=plot, labels=labels))

        self.container.add(p)
        self.container.invalidate_and_redraw()

    def _srcpath_changed(self):


        # default_radius=radius,
        # default_bounds=bounds,
        # convert_mm=convert_mm,
        # use_label=use_label,
        # make=make,
        # rotate=rotate)
        self._reload()

    def _rotation_changed(self):
        self._reload()

    def _reload(self):
        if self.initialized:
            self.container = self._container_factory()
            print os.path.isfile(self.srcpath), self.srcpath
            if os.path.isfile(self.srcpath):
                p = make_xml(self.srcpath,
                             default_bounds=(2.54, 2.54),
                             default_radius=0.0175 * 2.54,
                             rotate=self.rotation,
                             convert_mm=True)
                self.load(p)

    def _container_default(self):
        return self._container_factory()

    def _container_factory(self):
        return RotatingContainer(bgcolor='white')


def make_xml(path, offset=100, default_bounds=(50, 50),
             default_radius=3, convert_mm=False,
             make=True,
             use_label=True,
             rotate=0):
    """
        convert a csv into an xml

        use blank line as a group marker
        circle labels are offset by ``offset*group_id``
        ie. group 0. 1,2,3
            group 1. 101,102,103
    """
    out = '{}_from_csv.xml'.format(os.path.splitext(path)[0])
    if not make:
        return out

    root = Element('root')
    ul = Element('use_label')
    ul.text = 'True' if use_label else 'False'
    root.append(ul)

    outline = Element('outline')
    bb = Element('bounding_box')
    width, height = Element('width'), Element('height')
    width.text, height.text = map(str, default_bounds)
    bb.append(width)
    bb.append(height)

    outline.append(bb)
    root.append(outline)

    circles = Element('circles')
    radius = Element('radius')
    radius.text = str(default_radius)
    circles.append(radius)

    face_color = Element('face_color')
    face_color.text = 'white'
    circles.append(face_color)

    root.append(circles)

    i = 0
    off = 0
    reader = csv.reader(open(path, 'r'), delimiter=',')
    # writer = open(path + 'angles.txt', 'w')
    nwriter = None
    if rotate:
        nwriter = csv.writer(open(path + 'rotated_{}.txt'.format(rotate), 'w'))

    header = reader.next()
    if nwriter:
        nwriter.writerow(header)

    theta = math.radians(rotate)
    for k, row in enumerate(reader):
        # print k, row
        row = map(str.strip, row)
        if row:
            e = Element('point')
            x, y, l = Element('x'), Element('y'), Element('label')

            xx, yy = float(row[0]), float(row[1])
            try:
                r = float(row[2])
                rr = Element('radius')
                if convert_mm:
                    r *= 2.54

                rr.text = str(r)
                e.append(rr)
            except IndexError:
                r = None

            px = math.cos(theta) * xx - math.sin(theta) * yy
            py = math.sin(theta) * xx + math.cos(theta) * yy

            xx, yy = px, py
            if nwriter:
                data = ['{:0.4f}'.format(xx),
                        '{:0.4f}'.format(yy)]
                if r is not None:
                    data.append('{:0.4f}'.format(r))

                nwriter.writerow(data)

            if convert_mm:
                xx = xx * 2.54
                yy = yy * 2.54

            x.text = str(xx)
            y.text = str(yy)

            # a = math.degrees(math.atan2(yy, xx))
            # writer.write('{} {}\n'.format(k + 1, a))
            l.text = str(i + 1 + off)
            e.append(l)
            e.append(x)
            e.append(y)

            circles.append(e)
            i += 1
        else:
            # use blank rows as group markers
            off += offset
            i = 0

    tree = ElementTree(root)
    tree.write(out,
               xml_declaration=True,
               method='xml',
               pretty_print=True)
    return out


def open_txt(p, bounds, radius,
             use_label=True,
             convert_mm=False,
             make=True, rotate=None):
    gm = GraphicModel(srcpath=p, rotation=rotate or 0)
    p = make_xml(p,
                 default_radius=radius,
                 default_bounds=bounds,
                 convert_mm=convert_mm,
                 use_label=use_label,
                 make=make,
                 rotate=rotate)

    #    p = '/Users/ross/Sandbox/graphic_gen_from_csv.xml'
    gm.load(p)
    gm.initialized = True
    gcc = GraphicGeneratorController(model=gm)

    return gcc, gm


if __name__ == '__main__':
    gm = GraphicModel()
    # p = '/Users/ross/Sandbox/2mmirrad.txt'
    # p = '/Users/ross/Sandbox/2mmirrad_ordered.txt'
    # p = '/Users/ross/Sandbox/1_75mmirrad_ordered.txt'
    # p = '/Users/ross/Sandbox/1_75mmirrad_ordered.txt'
    # p = '/Users/ross/Pychrondata_diode/setupfiles/irradiation_tray_maps/0_75mmirrad_ordered1.txt'
    # p = '/Users/ross/Sandbox/1_75mmirrad.txt'
    p = '/Users/ross/Pychrondata_dev/setupfiles/irradiation_tray_maps/construction/newtrays/1_75mmirrad_continuous.txt'
    # p = '/Users/ross/Pychrondata_diode/setupfiles/irradiation_tray_maps/0_75mmirrad.txt'
    # p = '/Users/ross/Pychrondata_diode/setupfiles/irradiation_tray_maps/0_75mmirrad_continuous.txt'
    # p = '/Users/ross/Pychrondata_dev/setupfiles/irradiation_tray_maps/newtrays/2mmirrad_continuous.txt'
    # p = '/Users/ross/Pychrondata_dev/setupfiles/irradiation_tray_maps/newtrays/40_no_spokes.txt'
    # p = '/Users/ross/Pychrondata_dev/setupfiles/irradiation_tray_maps/newtrays/26_spokes.txt'
    # p = '/Users/ross/Pychrondata_dev/setupfiles/irradiation_tray_maps/newtrays/26_no_spokes.txt'
    # p = '/Users/ross/Pychrondata_dev/setupfiles/irradiation_tray_maps/construction/newtrays/40_spokes.txt'
    # p = '/Users/ross/Desktop/72_spokes'
    # p = '/Users/ross/Pychrondata_dev/setupfiles/irradiation_tray_maps/construction/newtrays/16_40_ms.txt'
    # p = '/Users/ross/Pychrondata_dev/setupfiles/irradiation_tray_maps/construction/newtrays/40_spokes_rev2.txt'
    # p = '/Users/ross/Pychrondata_dev/setupfiles/irradiation_tray_maps/construction/newtrays/40_spokes-5.txt'
    p = '/Users/ross/Pychrondata_dev/setupfiles/irradiation_tray_maps/construction/newtrays/24_spokes.txt'
    gcc, gm = open_txt(p, (2.54, 2.54), 0.03 * 2.54,
                       convert_mm=True, make=True,
                       rotate=0)

    #     p2 = '/Users/ross/Pychrondata_diode/setupfiles/irradiation_tray_maps/newtrays/TX_6-Hole.txt'
    #     gcc, gm2 = open_txt(p2, (2.54, 2.54), .1, make=False)

    #p2 = '/Users/ross/Pychrondata_diode/setupfiles/irradiation_tray_maps/newtrays/TX_20-Hole.txt'
    #gcc, gm2 = open_txt(p2, (2.54, 2.54), .1, make=False)


    #     gm2.container.bgcolor = 'transparent'
    #     gm2.container.add(gm.container)

    gcc.configure_traits()

# ============= EOF =============================================
