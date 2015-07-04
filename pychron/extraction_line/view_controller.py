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
from traits.api import HasTraits, \
    Str, Float, List, Any, Color, Property
from traitsui.api import View, Item, Group, HGroup, \
    TableEditor, Handler, RangeEditor
from traitsui.table_column import ObjectColumn

# =============standard library imports ========================
import os
import glob
import cPickle as pickle
import copy
# =============local library imports  ==========================

from pychron.paths import paths

def get_user_views():
    return glob.glob(os.path.join(paths.hidden_dir, 'userview*'))

class ViewControllerHandler(Handler):
    def closed(self, info, is_ok):
        '''

        '''

        # delete any previous view
        # if they exist they will be rewritten below

        for uvi in get_user_views():
            os.remove(uvi)

        obj = info.object.views
        for i, v in enumerate(obj):

            name = 'userview{}'.format(i)
            with open(os.path.join(paths.hidden_dir, name), 'w') as f:
                pickle.dump(v, f)

        super(ViewControllerHandler, self).closed(info, is_ok)


class UserView(HasTraits):
    '''
    '''
    x = Float
    y = Float
    z = Float
    rx = Float
    ry = Float
    rz = Float
    scene_graph = Any(transient=True)

    rmin = Float(0)
    rmax = Float(360)
    xmin = Float(-50)
    xmax = Float(10)
    ymin = Float(-50)
    ymax = Float(10)

    zoom = Property(depends_on='_zoom')
    _zoom = Float(1)
    zmin = Float(1)
    zmax = Float(100)
    name = Str
    key = Str

    background_color = Color
    def _get_zoom(self):
        return self._zoom / 0.02

    def _set_zoom(self, v):
        self._zoom = v * 0.02

    def _anytrait_changed(self, name, old, new):
        '''

        '''
        if self.scene_graph is not None:
            self.scene_graph.reset_view()
            self.scene_graph.root[0].translate = [self.x, self.y, self.z]

            m, rot = self.scene_graph.calc_rotation_matrix(self.rx, self.ry, self.rz)
            self.scene_graph.canvas.thisrotation = rot
            self.scene_graph.root[0].matrix = m
            self.scene_graph.root[0].scale = (self._zoom,) * 3  # (self.zoom * 0.02,)*3

            try:
                self.scene_graph.root[1].matrix = m
            except IndexError:
                pass
            color = [c / 255.0 for c in self.background_color]
            self.scene_graph.canvas.set_background_color(color)

            self.scene_graph.canvas.Refresh()


class ViewController(HasTraits):
    '''
    '''
    views = List

    scene_graph = Any  # (transient = True)
#    def __init__(self, *args, **kw):
#        super(ViewController, self).__init__(*args, **kw)
    def _views_default(self):
        return self.views_factory()

#    def _bu_fired(self):
#        '''
#        '''
#        self.views.append(UserView(name = 'view1', key = 'v', scene_graph = self.scene_graph))
#    def _views_default(self):
#        '''
#        '''

    def views_factory(self):
        '''
        '''
        # if os.path.exists(picklepath):

        uvfs = get_user_views()
        if uvfs:
            px = []
            for pa in uvfs:
                with open(pa, 'r') as f:
                    try:
                        pi = pickle.load(f)
                        pi.scene_graph = self.scene_graph
                        px.append(pi)
                    except ImportError:
                        pass
            return px
        else:
            return []  # UserView(name = 'home', key = 'h', scene_graph = self.scene_graph)]

    def _scene_graph_changed(self):
        for v in self.views:
            v.scene_graph = self.scene_graph

    def row_factory(self):
        '''
        '''
        if len(self.views):
            v = copy.copy(self.views[-1])
            v.scene_graph = self.scene_graph
            v.name = 'userview{}'.format(len(self.views) + 1)
        else:
            v = UserView(scene_graph=self.scene_graph, name='userview1')

        self.scene_graph.canvas.user_views.append(v)

    def _table_editor_factory(self):
        '''
        '''
        col = [ObjectColumn(name='name'),
             ObjectColumn(name='key')]
        return TableEditor(columns=col,
                           auto_size=False,
                           orientation='vertical',
                           show_toolbar=True,
                           row_factory=self.row_factory,
                           deletable=True,
                           edit_view=View(
                                            Group(
                                                HGroup('name', 'key'),
                                                Item('x', editor=RangeEditor(low_name='xmin',
                                                                            high_name='xmax',
                                                                            mode='slider')),
                                                Item('y', editor=RangeEditor(low_name='xmin',
                                                                            high_name='xmax',
                                                                            mode='slider')),
                                                Item('z', editor=RangeEditor(low_name='xmin',
                                                                            high_name='xmax',
                                                                            mode='slider')),
                                                Item('rx', editor=RangeEditor(low_name='rmin',
                                                                             high_name='rmax',
                                                                             mode='slider')),
                                                Item('ry', editor=RangeEditor(low_name='rmin',
                                                                             high_name='rmax',
                                                                             mode='slider')),
                                                Item('rz', editor=RangeEditor(low_name='rmin',
                                                                             high_name='rmax',
                                                                             mode='slider')),
                                                Item('zoom', editor=RangeEditor(low_name='zmin',
                                                                             high_name='zmax',
                                                                             mode='slider')),
                                                Group('background_color'
                                                      # , style = 'custom'
                                                      ),
                                                show_border=True,
                                                ),
                                          resizable=True,
                                          )
                           )
    def traits_view(self):
        '''
        '''
        return View(
                    Item('views',
                         height=75,
                         editor=self._table_editor_factory(), show_label=False),
                    resizable=True,
                    width=375,
                    height=675,
                    handler=ViewControllerHandler,
                    title='User Canvas Views'
                    )


if __name__ == '__main__':
    vm = ViewController()
    vm.configure_traits()
