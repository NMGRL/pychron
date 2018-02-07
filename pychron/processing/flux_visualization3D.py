# ===============================================================================
# Copyright 2018 ross
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
from traits.api import HasTraits, Instance, on_trait_change
from traitsui.api import View, UItem, Item
from mayavi.core.ui.api import MayaviScene, MlabSceneModel, SceneEditor
from numpy import linspace, meshgrid


class FluxVisualization3D(HasTraits):
    scene = Instance(MlabSceneModel, ())

    def update(self, x, y, z):
        print 'x', x
        print 'y', y
        print 'z', z
        self.scene.mlab.surf(z, warp_scale='auto')
        # self.scene.mlab.surf(x, y, z)

    # @on_trait_change('scene.activated')
    # def update_plot(self):
    #     # This function is called when the view is opened. We don't
    #     # populate the scene when the view is not yet open, as some
    #     # VTK features require a GLContext.
    #
    #     # We can do normal mlab calls on the embedded scene.
    #     self.scene.mlab.test_points3d()
    #
    #     r = 1
    #     n = 100
    #     xi = linspace(-r, r, n)
    #     yi = linspace(-r, r, n)
    #     XX, YY = meshgrid(xi, yi)

    # self.scene.mlab.surf(XX, YY)

    def traits_view(self):
        # the layout of the dialog screated
        v = View(Item('scene', editor=SceneEditor(scene_class=MayaviScene),
                      height=250, width=300, show_label=False),
                 resizable=True)
        return v


if __name__ == '__main__':
    v = FluxVisualization3D()
    v.configure_traits()
# ============= EOF =============================================
