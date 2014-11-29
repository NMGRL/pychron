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



# =============enthought library imports=======================
from traits.api import  List
from traitsui.table_column import ObjectColumn
# ============= standard library imports ========================

# ============= local library imports  ==========================
from pychron.graph.editors.plot_editor import PlotEditor
from pychron.graph.editors.diffusion_series_editor import  \
    SpectrumSeriesEditor, ChistSeriesEditor, UnchistSeriesEditor, \
    LogrroSeriesEditor, ArrheniusSeriesEditor
from traitsui.extras.checkbox_column import CheckboxColumn
# from chaco.polygon_plot import PolygonPlot
# from chaco.contour_poly_plot import ContourPolyPlot
# from chaco.cmap_image_plot import CMapImagePlot
# from pychron.graph.editors.series_editor import ContourPolyPlotEditor
# from chaco.base_xy_plot import BaseXYPlot
# from chaco.contour_line_plot import ContourLinePlot
# from chaco.base_contour_plot import BaseContourPlot


class DiffusionPlotEditor(PlotEditor):
    _series_editors = List
    iscoolinghistory = False
    isspectrum = False
    def _build_series_editors(self):
        self.series_editors = []
        plots = self._get_plots()

        plot = None
        iscoolinghistory = False
        isspectrum = False
        isunconstrained_thermal_history = False
        name = None
        for i, rid in enumerate(self.graph.runids):

            plotname = lambda x: x.format(rid)
            isplottype = lambda x: plotname(x) in plots
            if isplottype('{}.chist.l'):
                iscoolinghistory = True
                self.iscoolinghistory = True
                name = plotname('{}.chist')
                plot = plots[plotname('{}.chist.l')][0]

                editor = ChistSeriesEditor

            elif isplottype('{}.unchist'):
#                isunconstrained_thermal_history = True
                name = plotname('{}.unchist')
                editor = UnchistSeriesEditor
            elif isplottype('{}.logr_ro.meas'):
                name = plotname('{}.logr_ro')
                editor = LogrroSeriesEditor
                plot = plots[plotname('{}.logr_ro.meas')][0]
            elif isplottype('{}.arr.meas'):
                name = plotname('{}.arr.meas')
                plot = plots[plotname('{}.arr.meas')][0]
                editor = ArrheniusSeriesEditor
            else:
                self.isspectrum = True
                isspectrum = True
                name = plotname('{}.spec.meas')
                plot = plots[plotname('{}.spec.meas')][0]
                editor = SpectrumSeriesEditor

            kwargs = self._get_series_editor_kwargs(plot, i)
            kwargs['runid'] = rid
#            kwargs['isspectrum'] = isspectrum
#            kwargs['iscoolinghistory'] = iscoolinghistory
            kwargs['_name'] = name

#            editor = None
#            if iscoolinghistory:
#                if isunconstrained_thermal_history:
#
#            elif isspectrum:
#            elif isinstance(plot, BaseXYPlot):
#                editor = DiffusionSeriesEditor
# #
            if editor:
                self.series_editors.append(editor(**kwargs))

        if plot:
            self._sync_limits(plot)

#    def _get_additional_groups(self):
#        cols = [ObjectColumn(name='name', editable=False),
#                CheckboxColumn(name='show')]
#        table_editor = TableEditor(columns=cols,
#                                   selected='_selected',
#                                   selection_mode='row')
#        grp = Item('_series_editors',
#                 editor=table_editor,
#                 style='custom',
#                 show_label=False
#
#                 )
#        return grp

#            super(DiffusionPlotEditor,self)._build_series_editors(editors=self._series_editors)
#
#    def _get_plots(self):
#        p=super(DiffusionPlotEditor,self)._get_plots()
#        ps=dict()
#        for i in range(3):
#            k='plot{}'.format(i)
#            ps[k]=p[k]
#        return ps

#    def _get_selected_group(self):
#        grp=Item('_series_editors',
#                 editor=ListEditor(use_notebook=True,
#                            dock_style='tab',
#                            page_name='.name'),
#                 style='custom',
#                 show_label=False)
#        return grp
    def _get_table_columns(self):
        if self.iscoolinghistory:
            return [ObjectColumn(name='runid', editable=False),
                    CheckboxColumn(name='inner', label='Inner'),
                    CheckboxColumn(name='outer', label='Outer'),
                    ]
        else:
            cols = [ObjectColumn(name='runid', editable=False),
                CheckboxColumn(name='show_sample', label='Sample'),
                CheckboxColumn(name='show_model', label='Model')]
            if self.isspectrum:
                cols.append(CheckboxColumn(name='show_inverse_model', label='Inv. Model'))
            return cols



#            plot = plots['plot{}'.format(i)][0]
#            _name, plot = plots.popitem()
#            plot = plot[0]
#            if isinstance(plot, PolygonPlot):
#                if isinstance(plots['plot{}'.format(i + 1)][0], PolygonPlot):
#                    self.iscoolinghistory = True
#                    isspectrum = False
#                elif not isinstance(plot, ContourPolyPlot):
#                    isspectrum = True
#                    i += 1
#
# #                plot = plots['plot{}'.format(i)][0]
#
# #                elif isinstance(plot, CMapImagePlot):
#            elif isinstance(plot, BaseContourPlot):
#                self.isunconstrained_thermal_history = True
#                isspectrum = False
# #                    i+=1
# #                    plot=plots['plot{}'.format(i)][0]
#
# ============= EOF =====================================
