#===============================================================================
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
#===============================================================================

#============= enthought library imports =======================
from traits.api import HasTraits, Instance, List
from traitsui.api import View, UItem
# from pychron.envisage.tasks.base_editor import BaseTraitsEditor
# from pychron.processing.tasks.analysis_edit.graph_editor import GraphEditor
# from pychron.graph.graph import Graph
# from pychron.regression.least_squares_regressor import LeastSquaresRegressor
#============= standard library imports ========================
# import math
from numpy import average, asarray, cos, linspace, pi, array, max, min, zeros, \
    mgrid
# import struct
# from collections import namedtuple
# from pychron.processing.tasks.analysis_edit.interpolation_editor import InterpolationEditor
# from pychron.graph.error_bar_overlay import ErrorBarOverlay
from pychron.regression.ols_regressor import MultipleLinearRegressor
# from pychron.ui.mpl_editor import MPLFigureEditor
from pychron.processing.tasks.flux.flux_editor import FluxEditor
#============= local library imports  ==========================
class FluxTool(HasTraits):
    def traits_view(self):
        v = View()
        return v

# Position = namedtuple('Positon', 'position x y')

from mayavi.core.ui.api import MayaviScene, MlabSceneModel, \
       SceneEditor
# import numpy as np
class FluxEditor3D(FluxEditor):
    scene = Instance(MlabSceneModel, ())
    actors = List
    _ax = None
    def _rebuild_graph(self):
        if not self._references:
            return

        if self.actors:
            for ai in self.actors:
                ai.remove()
            self.actors = []

        xy = self._get_xy(self._references)
        ys, es = self._get_flux(self._references)
        reg = MultipleLinearRegressor(xs=xy, ys=ys, yserr=es, fit='linear')

        xy = array(xy)
        r, _ = xy.shape
        x, y = xy.T

        w = (max(x) - min(x))

        xmin = ymin = -w - 1
        xmax = ymax = w + 1

        xx, yy = mgrid[xmin:xmax, ymin:ymax]

        z = zeros((r, r))
        zl = zeros((r, r))
        zu = zeros((r, r))
        error_exaggeration = 25
        for i in range(r):
            for j in range(r):
                pt = (xx[i, j],
                      yy[i, j])
                v = reg.predict([pt])[0]
                e = reg.predict_error([pt])[0] * error_exaggeration
                zl[i, j] = v - e
                zu[i, j] = v + e
                z[i, j] = v

        ws = 10000
        mlab = self.scene.mlab
#        radius = 0.1
#        for xi, yi, zi, ei, ri in zip(x, y, array(ys) * ws,
#                                  array(es) * error_exaggeration * ws,
#                                  (radius,) * len(x)
#                                  ):
#            print xi, yi
#            pt = mlab.plot3d([xi, xi], [yi, yi],
#                             [zi - ei, zi + ei],
#                             tube_radius=ri,
#                             tube_sides=8
#                             )
#            self.actors.append(pt)

        fsurf = mlab.surf(xx, yy, z,
                                     warp_scale=ws,
                                     extent=[xmin, xmax, ymin, ymax, min(z), max(z)]
                                     )
        self.actors.append(fsurf)

        usurf = mlab.surf(xx, yy, zu, warp_scale=ws, color=(1, 0, 0),
                                     extent=[xmin, xmax, ymin, ymax, min(z), max(z)],
                             opacity=0.35,
                             transparent=True)
        self.actors.append(usurf)

        lsurf = mlab.surf(xx, yy, zl, warp_scale=ws, color=(1, 0, 0),
                                     extent=[xmin, xmax, ymin, ymax, min(z), max(z)],
                             opacity=0.35,
                             transparent=True)
        self.actors.append(lsurf)
        if not self._ax:
            self._ax = mlab.axes(
                             xlabel='X mm',
                             ylabel='Y mm',
                             ranges=[xmin, xmax, ymin, ymax, min(z), max(z)]
                             )


    def traits_view(self):
        v = View(UItem('scene', style='custom',
                       height=250, width=600,
                       resizable=True,
                       editor=SceneEditor(scene_class=MayaviScene)))
        return v

#============= EOF =============================================
