# ===============================================================================
# Copyright 2013 Jake Ross
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
from traits.api import Instance
from traitsui.api import View, UItem
from chaco.plot_containers import HPlotContainer
from enable.component_editor import ComponentEditor
from chaco.plot import Plot
from chaco.array_plot_data import ArrayPlotData
from chaco.default_colormaps import hot
# ============= standard library imports ========================
from numpy import ones, asarray
# ============= local library imports  ==========================
from pychron.image.cv_wrapper import grayspace
from pychron.viewable import Viewable


class MVImage(Viewable):
    container = Instance(HPlotContainer)
    plotdata = Instance(ArrayPlotData)

    def setup_images(self, n, wh):
        self.container._components = []
        self.plotdata = plotdata = ArrayPlotData()
        for i in range(n):
            plot = Plot(plotdata, padding=0, default_origin="top left")

            name = 'imagedata{:03d}'.format(i)
            plotdata.set_data(name, ones(wh))

            plot.img_plot(name, colormap=hot)
            self.container.add(plot)

        self.container.request_redraw()

    def set_image(self, arr, idx=0):
        arr = asarray(grayspace(arr))

        self.plotdata.set_data('imagedata{:03d}'.format(idx), arr)
        # invoke_in_main_thread(self.container.invalidate_and_redraw)
#         self.container.invalidate_and_redraw()
        self.container.request_redraw()

    def _container_default(self):
        hp = HPlotContainer(padding=0, spacing=0)
        return hp

    def traits_view(self):
        v = View(UItem('container', editor=ComponentEditor()),
                 resizable=True,
                 handler=self.handler_klass)
        return v
# ============= EOF =============================================
