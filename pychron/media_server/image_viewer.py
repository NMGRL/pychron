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
from traits.api import HasTraits, Instance, Any
from traitsui.api import View, Item, TableEditor
from chaco.api import HPlotContainer, ArrayPlotData, Plot
#============= standard library imports ========================
import os
#============= local library imports  ==========================
from pychron.graph.image_underlay import ImageUnderlay
from pychron.graph.tools.xy_inspector import XYInspector, XYInspectorOverlay

class ImageViewer(HasTraits):
    container = Instance(HPlotContainer, ())
    plot = Any

    def load_image(self, path):
        if os.path.isfile(path):
            with open(path, 'r') as fp:
                self.set_image(fp)

    def set_image(self, buf):
        '''
            buf is a file-like object
        '''
        self.container = HPlotContainer()
        pd = ArrayPlotData(x=[0, 640],
                           y=[0, 480])
        padding = [30, 5, 5, 30]
        plot = Plot(data=pd, padding=padding,
#                    default_origin=''
                    )
        self.plot = plot.plot(('x', 'y'),)[0]
        self.plot.index.sort_order = 'ascending'
        imo = ImageUnderlay(self.plot,
                            padding=padding,
                            path=buf)
        self.plot.overlays.append(imo)

        self._add_tools(self.plot)

        self.container.add(plot)
        self.container.request_redraw()

    def _add_tools(self, plot):
        inspector = XYInspector(plot)
        plot.tools.append(inspector)
        plot.overlays.append(XYInspectorOverlay(inspector=inspector,
                                                component=plot,
                                                align='ul',
                                                bgcolor=0xFFFFD2
                                                ))

#        zoom = ZoomTool(component=plot,
#                        enable_wheel=False,
#                        tool_mode="box", always_on=False)
#        pan = PanTool(component=plot, restrict_to_data=True)
#        plot.tools.append(pan)
#
#        plot.overlays.append(zoom)

#============= EOF =============================================
