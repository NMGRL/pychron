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
from traits.api import HasTraits, Instance
from traitsui.api import View, Item
from tvtk.pyface.scene_editor import SceneEditor
from tvtk.pyface.api import Scene
from mayavi.core.ui.mayavi_scene import MayaviScene
from mayavi.tools.mlab_scene_model import MlabSceneModel
# ============= standard library imports ========================

# ============= local library imports  ==========================


def point_generator(padding, cx, cy):
    offset = 1
    # nrows should be calculates so  result is a square
    nrows = int(padding * 2 / offset) + 1

    for i in range(nrows):
        y = cy - padding + i * offset
        if i % 2:
            p1 = cx - padding, y
            p2 = cx + padding, y
        else:
            p2 = cx - padding, y
            p1 = cx + padding, y

        yield p1, p2


class Graph3D(HasTraits):
    scene = Instance(MlabSceneModel, ())
#    def _scene_default(self):
#        s = MlabSceneModel()
#        pt_gen = point_generator(5, 0, 0)
#        j = 0
#        xx = []
#        yy = []
#        zz = []
#        for p1, p2 in [((-5, 0), (5, 0)), ((5, 1), (-5, 1))]:
# #        for p1, p2 in pt_gen:
#
#            #move to p1
#            #move to p2
#            moving = True
#            i = 0
#            zs = []
#            xs = []
#            ys = []
#            while moving:
#                if i == 11:
#                    break
#
#                x = p1[0] - i if j % 2 else p1[0] + i
#                mag = 40 - x * x
#                zs.append(mag)
#
#                xs.append(x)
#                ys.append(p1[1])
#
#                if j % 2:
#                    data = sorted(zip(xs, ys, zs), key = lambda d:d[0])
#
#                    xs = [d[0] for d in data]
#                    ys = [d[1] for d in data]
#                    zs = [d[2] for d in data]
#
#                i += 1
#            j += 1
#            xx.append(xs)
#            yy.append(ys)
#            zz.append(zs)
#
#        s.mlab.mesh(asarray(xx), asarray(yy), asarray(zz))
# #        s.mlab.plot3d(asarray(xx)[0], asarray(yy)[0], asarray(zz)[0], asarray(zz)[0])
#        return s
#        xs = []
#        ys = []
#        zs = []
#        for i in range(5):
#
#            x = linspace(-5, 5, 100)
#            y = ones(100) * i
#            z = 10 - 0.2 * x * x
#            xs.append(x)
#            ys.append(y)
#            zs.append(z)
#
#        s.mlab.mesh(asarray(xs), asarray(ys), asarray(zs)
#                        #z,
# #                          line_width = 50,
# #                          tube_radius = None,
#                          #representation = 'wireframe'
#                          )
#        return s
    def clear(self):
        self.scene.mlab.clf()

    def plot_data(self, z, func='surf', outline=True,
                  **kw):

        mlab = self.scene.mlab
        getattr(mlab, func)(z, **kw)

        if outline:
            mlab.outline()

    def plot_surf(self, *args, **kw):
        mlab = self.scene.mlab
        mlab.surf(*args, **kw)
        mlab.outline()
        mlab.axes()


    def plot_points(self, x, y, z, color=None):
        mlab = self.scene.mlab
        if color:
            pts = mlab.points3d(x, y, z, z, scale_mode='none', scale_factor=0.1)
        else:
            pts = mlab.points3d(x, y, z, scale_mode='none', scale_factor=0.1)
        mesh = mlab.pipeline.delaunay2d(pts)
        mlab.pipeline.surface(mesh)

    def plot_lines(self, x, y, z):
        import numpy as np
#        n_mer, n_long = 6, 11
#        pi = numpy.pi
#        dphi = pi / 1000.0
#        phi = numpy.arange(0.0, 2 * pi + 0.5 * dphi, dphi)
#        mu = phi * n_mer
#        x = numpy.cos(mu) * (1 + numpy.cos(n_long * mu / n_mer) * 0.5)
#        y = numpy.sin(mu) * (1 + numpy.cos(n_long * mu / n_mer) * 0.5)
#        print x
#        z = numpy.sin(n_long * mu / n_mer) * 0.5
#
#        l = self.scene.mlab.plot3d(x, y, z, numpy.sin(mu), tube_radius=0.025, colormap='Spectral')
#        return l

        x = np.array(x)
        y = np.array(y)
        z = np.array(z)
        self.scene.mlab.plot3d(x, y, z)

    def traits_view(self):
#        self.scene.mlab.points3d(x, y, z)
        kw = dict()
        klass = Scene

        use_mayavi_toolbar = True
        use_raw_toolbar = False
        if use_mayavi_toolbar:
            klass = MayaviScene
        elif use_raw_toolbar:
            klass = None

        if klass is not None:
            kw['scene_class'] = klass

        v = View(Item('scene', show_label=False,
                      height=400,
                      width=400,
                      resizable=True,
                      editor=SceneEditor(**kw


                                           )))
        return v

# ============= EOF ====================================
# if __name__ == '__main__':
#    g = FastScan()
#    g.configure_traits()
# class FastScan(HasTraits):
#    scan = Button
#    graph = Instance(Graph3D, ())
#    def _scan_(self):
#        padding = 20
#        s = self.graph.scene
#        pt_gen = point_generator(padding, 0, 0)
#        j = 0
#        xx = []
#        yy = []
#        zz = []
# #        for p1, p2 in [((5, -5), (-5, 5)), ((-5, -4), (5, -4))]:
# #            print p1, p2, pt_gen.next()
#        for p1, p2 in pt_gen:
#
#            #move to p1
#            #move to p2
#            moving = True
#            i = 0
#            zs = []
#            xs = []
#            ys = []
#            while moving:
#                if i == 2 * padding + 1:
#                    break
#
#                x = p1[0] - i if j % 2 == 0 else p1[0] + i
#                if i == 0 or i == 2 * padding:
#                    mag = 0
#                else:
#                    mag = (-0.1 * (j - padding) ** 2) + padding * 4 - 0.1 * x * x
#                zs.append(mag)
#
#                xs.append(x)
#                ys.append(p1[1])
#
#                if j % 2 == 0:
#                    data = sorted(zip(xs, ys, zs), key = lambda d:d[0])
#
#                    xs = [d[0] for d in data]
#                    ys = [d[1] for d in data]
#                    zs = [d[2] for d in data]
#
#                i += 1
#            j += 1
#            xx.append(xs)
#            yy.append(ys)
#            zz.append(zs)
# #            do_after(1, s.mlab.plot3d, asarray(xs), asarray(ys), asarray(zs), asarray(zs))#, asarray(zz)[0])
#            do_after(1, s.mlab.mesh, asarray(xx), asarray(yy), asarray(zz))
#            time.sleep(0.1)
#
#
#    def _scan_fired(self):
#        t = Thread(target = self._scan_)
#        t.start()
#
#
#
#    def traits_view(self):
#        v = View(
#
#
#                 Item('scan', show_label = False),
#                 Item('graph', show_label = False, style = 'custom'))
#        return v
