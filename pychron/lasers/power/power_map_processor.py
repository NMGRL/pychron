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
from traits.api import Bool, HasTraits, Instance
# from traitsui.api import View, Item, Group, HGroup, VGroup, HSplit, VSplit
# ============= standard library imports ========================
# from tables import open_file
from numpy import transpose, array, shape, max, linspace, rot90, \
    min
# ============= local library imports  ==========================
from pychron.graph.contour_graph import ContourGraph
from pychron.managers.data_managers.h5_data_manager import H5DataManager

from scipy.interpolate.ndgriddata import griddata
# from numpy.lib.function_base import percentile


class PowerMapProcessor(HasTraits):
    '''
    '''
    correct_baseline = Bool(False)
    color_map = 'hot'
    levels = 15
    interpolation_factor = 5
    graph = Instance(ContourGraph)

    def extract_attrs(self, attrs):
        rs = []
        for ai in attrs:
            rs.append(self._metadata[ai])

        return rs

    def set_percent_threshold(self, n):
        cg = self.graph
        args = self._measure_properties(self._data, self._metadata, n)
        if args:
            cg.plots[0].data.set_data('z0', args[1])

    def load_graph(self, reader, window_title=''):
        cg = ContourGraph(
            container_dict=dict(kind='h',
                                #                                               padding=40,
                                #                                               shape=(2, 2),
                                #                                               spacing=(12, 12)
            )
        )

        z, metadata = self._extract_power_map_data(reader)
        self._data = z
        self._metadata = metadata
        center_plot = cg.new_plot(
            add=False,
            padding=0,
            width=400,
            height=400,
            resizable=''
            #                             aspect_ratio=1
        )
        center_plot.index_axis.visible = False
        center_plot.value_axis.visible = False

        #         from skimage.morphology import label
        #         z = label(z)
        bounds = metadata['bounds']
        #center_plot, names, rd = cg.new_series(z=z, style='contour',
        cg.new_series(z=z, style='contour',
                      xbounds=bounds,
                      ybounds=bounds, )

        bottom_plot = cg.new_plot(
            add=False,
            height=150,
            resizable='h',
            padding=0,
            xtitle='mm',
            ytitle='power')

        right_plot = cg.new_plot(
            add=False,
            width=150,
            resizable='v',
            padding=0,
            xtitle='mm',
            ytitle='power')
        right_plot.x_axis.orientation = 'right'
        #         right_plot.x_axis.title = 'mm'
        right_plot.y_axis.orientation = 'top'
        #         right_plot.y_axis.title = 'power'

        center = center_plot.plots['plot0'][0]
        options = dict(style='cmap_scatter',
                       type='cmap_scatter',
                       marker='circle',
                       color_mapper=center.color_mapper)

        cg.new_series(plotid=1, render_style='connectedpoints')
        cg.new_series(plotid=1, **options)

        right_plot.x_axis.orientation = 'right'
        right_plot.y_axis.orientation = 'top'

        right_plot.x_axis.mapper = center_plot.value_mapper
        right_plot.y_axis.mapper = bottom_plot.value_mapper
        right_plot.x_axis.axis_line_visible = False
        right_plot.y_axis.axis_line_visible = False

        s = cg.new_series(plotid=2, render_style='connectedpoints')[0]
        s.orientation = 'v'
        s = cg.new_series(plotid=2, **options)[0]
        s.orientation = 'v'

        center.index.on_trait_change(cg.metadata_changed,
                                     'metadata_changed')

        cg.show_crosshairs('blue')

        #         z = self._plot_properties(z, metadata, cg)
        #         cg.plots[0].data.set_data('z0', z)


        gridcontainer = cg._container_factory(kind='g',
                                              padding=40,
                                              shape=(2, 2),
                                              spacing=(12, 12))

        gridcontainer.add(center_plot)
        gridcontainer.add(right_plot)
        gridcontainer.add(bottom_plot)

        cb = cg.make_colorbar(center)
        cb.width = 50
        cb.padding_left = 50

        cg.plotcontainer.add(cb)
        cg.plotcontainer.add(gridcontainer)

        self.graph = cg
        return cg

    def _measure_properties(self, z, metadata, p=25):
        from skimage.measure._regionprops import regionprops

        nim = z.copy()
        #         nz = z[z > min(z) * 3]

        #         for zi in z:
        #             print zi

        mz = min(z)
        r = max(z) - mz
        t = p * 0.01 * r + mz
        #         print 'aaaa', max(z), min(z)
        #         print 'bbbb', t, p
        #         t2 = percentile(nz, p)
        #         t = percentile(z, p)
        #         print 'nz ', t2, 'z ', t1
        nim[z < t] = 0

        props = None
        try:
            props = regionprops(nim.astype(int), ['EquivDiameter', 'Centroid',
                                                  'MajorAxisLength', 'MinorAxisLength',
                                                  'Orientation'
            ])
        except TypeError, e:
            pass
        return props, nim

    def _extract_properties(self, z, prop, metadata):
        r, c = prop['Centroid']

        rr, cc = z.shape
        #         print r, c
        b = metadata['bounds']
        scale = rr / (b[1] - b[0])

        cx = c / scale + b[0]
        cy = r / scale + b[0]
        #         print cx, cy
        radius = prop['EquivDiameter'] / (2. * scale)
        return cx, cy, radius, scale

    def _extract_power_map_data(self, reader):
        '''
        '''
        if isinstance(reader, H5DataManager):
            d = self._extract_h5(reader)
        else:
            d = self._extract_csv(reader)

        return d

    def _extract_h5(self, dm):
        #         cells = []
        tab = dm.get_table('power_map', '/')
        metadata = dict()
        try:
            b = tab._v_attrs['bounds']
        except Exception, e:
            print 'exception', e
            b = 1

        metadata['bounds'] = -float(b), float(b)

        try:
            bd = tab._v_attrs['beam_diameter']
        except Exception, e:
            print 'exception', e
            bd = 0

        try:
            po = tab._v_attrs['power']
        except Exception, e:
            print 'exception', e
            po = 0

        metadata['beam_diameter'] = bd
        metadata['power'] = po

        xs, ys, power = array([(r['x'], r['y'], r['power'])
                               for r in tab.iterrows()]).T

        #        xs, ys, power = array(xs), array(ys), array(power)
        #        n = power.shape[0]
        #        print n
        xi = linspace(min(xs), max(xs), 50)
        yi = linspace(min(ys), max(ys), 50)

        X = xi[None, :]
        Y = yi[:, None]

        power = griddata((xs, ys), power, (X, Y),
                         fill_value=0,
                         #                          method='cubic'
        )
        return rot90(power, k=2), metadata

    #        return flipud(fliplr(power)), metadata
    #        for row in tab.iterrows():
    #            x = int(row['col'])
    #            try:
    #                nr = cells[x]
    #            except IndexError:
    #                cells.append([])
    #                nr = cells[x]
    #
    #            # baseline = self._calc_baseline(table, index) if self.correct_baseline else 0.0
    #            baseline = 0
    #            pwr = row['power']
    #
    #            nr.append(max(pwr - baseline, 0))
    #
    #        d = len(cells[-2]) - len(cells[-1])
    #
    #        if d:
    #            cells[-1] += [0, ] * d
    #
    #        cells = array(cells)
    #        # use interpolation to provide smoother interaction
    #        cells = ndimage.interpolation.zoom(cells, self.interpolation_factor)
    #
    #        return rot90(cells, k=2), metadata
    def _extract_csv(self, reader):
        cells = []
        metadata = []
        reader_meta = False
        for _index, row in enumerate(reader):

            if reader_meta:
                metadata.append(row)
                continue
            if '<metadata>' in row[0]:
                reader_meta = True
                continue
            if '</metadata>' in row[0]:
                reader_meta = False
                continue

            x = int(row[0])

            try:
                nr = cells[x]
            except:
                cells.append([])
                nr = cells[x]

            # baseline = self._calc_baseline(table, index) if self.correct_baseline else 0.0
            baseline = 0
            try:
                pwr = row['power']
            except:
                pwr = float(row[2])
            nr.append(max(pwr - baseline, 0))



        # metadata now is supposed to be a dict
        md = dict(bounds=(-float(metadata[1][1]), float(metadata[1][1])))

        # rotate the array
        return rot90(array(cells), k=2), md

    def _calc_baseline(self, table, index):
        '''
        '''

        try:
            b1 = table.attrs.baseline1
            b2 = table.attrs.baseline2
        except:
            b1 = b2 = 0
            #        print b1,b2
        #    ps=[row['power'] for row in table]
        #    b1=ps[0]
        #    b2=ps[-1:][0]
        size = table.attrs.NROWS - 1

        bi = (b2 - b1) / size * index + b1

        return bi

    def _prep_2D_data(self, z):
        '''
     
        '''
        z = transpose(z)
        #        print z
        mx = float(max(z))

        #        z = array([100 * x / mx for x in [y for y in z]])

        r, c = shape(z)
        x = linspace(0, 1, r)
        y = linspace(0, 1, c)
        return x, y, z

# if __name__ == '__main__':
#    p=PowerMapViewer()
#
#    pa=sys.argv[1]
#    if pa[-2:]!='.h5':
#        pa+='.h5'
#
#
#    pa=os.path.join(paths.data_dir,'powermap',pa)
#    if os.path.isfile(pa):
#        p.open_power_map(pa)
# ============= EOF ====================================
#     def _plot_properties(self, z, metadata, cg):
# #         for prop in props:
# #         for pp in (25, 50, 75, 95):
#         for pp in (95,):
#             props, nim = self._measure_properties(z, metadata, p=pp)
#             for prop in props:
#                 cx, cy, radius, scale = self._extract_properties(z, prop, metadata)
#                 s = cg.new_series(x=[cx], y=[cy], type='scatter', marker='circle')
#     #             theta = linspace(-pi, pi)
#     #             xs = cx + radius * cos(theta)
#     #             ys = cy + radius * sin(theta)
#
#     #             s = cg.new_series(x=xs, y=ys)
#
#                 mal = prop['MajorAxisLength'] / scale * 0.5
#                 mil = prop['MinorAxisLength'] / scale * 0.5
#
#                 theta = prop['Orientation']
#                 x1 = cx + math.cos(theta) * mal
#                 y1 = cy - math.sin(theta) * mal
#
#                 x2 = cx - math.sin(theta) * mil
#                 y2 = cy - math.cos(theta) * mil
#
#                 cg.new_series([cx, x1], [cy, y1],
#                               color=s.color,
#                               line_width=2)
#                 cg.new_series([cx, x2], [cy, y2],
#                               color=s.color,
#                               line_width=2
#                               )
#
#                 ts = linspace(0, 2 * pi)
#
#                 cos_a, sin_a = cos(theta), sin(theta)
#
#                 eX = mil * cos(ts) * cos_a - sin_a * mal * sin(ts) + cx
#                 eY = mil * cos(ts) * sin_a + cos_a * mal * sin(ts) + cy
#
#                 cg.new_series(eX, eY,
#                               color=s.color
#                               )
#         return nim
#            try:
#                x = int(row['col'])
#            except:
#                try:
#                    x = int(row['x'])
#                except:
#     def load_graph2(self, reader, window_title=''):
#         '''
#         '''
#
#
#
# #        x, y, z = self._prep_2D_data(z)
# #        print x, y, z
#         w = 300
#         h = 300
#         bounds = metadata['bounds']
#         cplot = cg.new_plot(
#                             add=False,
#                             aspect_ratio=1,
#                             padding_top=0
# #                             padding_top=15,
# #                             padding_left=20,
# #                             padding_right=5,
# #                             resizable='',
# #                             bounds=[w, h],
#                           )
# #         cplot.width = 400
# #         cplot.height = 400
#
#
#         cplot.index_axis.title = 'mm'
#         cplot.value_axis.title = 'mm'
#
#         plot, names, rd = cg.new_series(x=[], y=[], z=z, style='contour',
#                       xbounds=bounds,
#                       ybounds=bounds,
#                       cmap=self.color_map,
# #                      colorbar=True,
#                       levels=self.levels)
#
#         cb = cg.make_colorbar(plot.plots['plot0'][0])
#         cb.padding_bottom = 55
#         cb.padding_top = 140
#
#         cg.new_series(x=[cx], y=[cy], type='scatter')
#         theta = linspace(-pi, pi)
#         radius = props[0]['EquivDiameter'] / (2.*scale)
# #         circle_y = radius * (cos(circle_x) - sin(circle_x))
#         xs = cx + radius * cos(theta)
#         ys = cy + radius * sin(theta)
#
#         cg.new_series(x=xs, y=ys)
#
# #        # plot max location
# #        from scipy.ndimage import maximum_position
# #        xm, ym = maximum_position(z)
# #        f = lambda a, i: [a[i] * abs(bounds[0] - bounds[1]) + bounds[0]]
# #        cg.new_series(x=f(x, xm), y=f(y, ym), type='scatter',
# #                      marker='plus',
# #                      color='black')
# #
#         cpolyplot = cplot.plots['plot0'][0]
#         options = dict(style='cmap_scatter',
#                      type='cmap_scatter',
#                      marker='circle',
#                      color_mapper=cpolyplot.color_mapper
#                      )
#
#         p_xaxis = cg.new_plot(
#                               add=False,
#                               padding_bottom=0,
# #                               padding_left=20,
# #                             padding_right=5,
# #                             padding_top=30,
#                             resizable='h',
# #                             halign='center',
# #                             height=100,
# #                             aspect_ratio=w / 100.,
#                             bounds=[w, 100],
#                             title='Power Map'
#                             )
#
#         p_xaxis.index_axis.visible = False
#         p_xaxis.value_axis.title = 'Power (%)'
#         cg.new_series(plotid=1, render_style='connectedpoints')
#         cg.new_series(plotid=1, **options)
#
#         p_yaxis = cg.new_plot(add=False,
#                               orientation='v',
#                               padding_left=0,
#                               padding_bottom=55,
#                               padding_top=0,
# #                               padding_top=140,
#                             resizable='v',
#                             bounds=[120, h]
#                              )
#
#         p_yaxis.index_axis.visible = False
#         p_yaxis.value_axis.title = 'Power (%)'
# #
#         cg.new_series(plotid=2, render_style='connectedpoints')
#         cg.new_series(plotid=2, **options)
# #
# #        ma = max([max(z[i, :]) for i in range(len(x))])
# #        mi = min([min(z[i, :]) for i in range(len(x))])
# #
# #        cg.set_y_limits(min=mi, max=ma, plotid=1)
# #        cg.set_y_limits(min=mi, max=ma, plotid=2)
#
#         cg.show_crosshairs()
# #
#         cpolyplot.index.on_trait_change(cg.metadata_changed,
#                                            'metadata_changed')
#
#         container = cg._container_factory(kind='v',
#                                           spacing=0,
#                                           fill_padding=True,
#                                           bgcolor='green',
#                                         aspect_ratio=w / 400.
# #                                           halign='right',
# #                                           halign='right',
# #                                          bounds=[w, h],
# #                                          resizable=''
#                                           )
#
# # #        print type(container)
#         container.add(cplot)
#         container.add(p_xaxis)
#
#
#         vc = VPlotContainer(stack_order='top_to_bottom',
#                             aspect_ratio=0.25,
#                             fill_padding=True,
#                             bgcolor='blue'
#                             )
#
#         from enable.component import Component
#         spacer = Component(bounds=[100, 100],
#                            resizable='',
#                            bgcolor='red')
# #         vc.add(spacer)
#         vc.add(p_yaxis)
#
#         cg.plotcontainer.spacing = 0
# #         cg.plotcontainer.halign = 'left'
#         cg.plotcontainer.add(container)
#         cg.plotcontainer.add(vc)
# #         cg.plotcontainer.add(cb)
#         cg.plotcontainer.resizable = ''
#
#         return cg
