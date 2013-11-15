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
import struct
from enable.component_editor import ComponentEditor
from traits.api import HasTraits, Str, List, Float, Any, Int, Instance
from traitsui.api import View, Item, EnumEditor, HGroup, VGroup, UItem
from pychron.canvas.canvas2D.irradiation_canvas import IrradiationCanvas
#============= standard library imports ========================
#============= local library imports  ==========================

def load_holder_canvas(canvas, geom):
    if geom:
        canvas = canvas
        holes = [(x, y, r, str(c + 1))
                 for c, (x, y, r) in iter_geom(geom)]
        canvas.load_scene(holes)


def iter_geom(geom):
    f = lambda x: struct.unpack('>fff', geom[x:x + 12])
    return ((i, f(gi)) for i, gi in enumerate(xrange(0, len(geom), 12)))


class Level(HasTraits):
    name = Str
    tray = Str
    z = Float
    trays = List
    db = Any
    level_id = Int
    canvas = Instance(IrradiationCanvas, ())
    geometry = Any

    def load(self, irrad):
        db = self.db
        if not isinstance(irrad, (str, unicode)):
            irrad = irrad.name

        with db.session_ctx():
            level = db.get_irradiation_level(irrad, self.name)
            self.level_id = int(level.id)
            if level.holder:
                name = level.holder.name

                if name in self.trays:
                    self.tray = name

            z = level.z
            self.z = z if z is not None else 0


    def _tray_changed(self):
        with self.db.session_ctx():
            holder = self.db.get_irradiation_holder(self.tray)
            if holder:
                self.geometry = holder.geometry

    def _geometry_changed(self):
        load_holder_canvas(self.canvas, self.geometry)

    def edit_db(self):
        db = self.db
        with db.session_ctx():
            level = db.get_irradiation_level_byid(self.level_id)

            level.name = self.name
            level.z = self.z
            holder = db.get_irradiation_holder(self.tray)
            if holder:
                level.holder = holder

    def traits_view(self):
        v = View(VGroup(
            HGroup(Item('name'),
                   Item('z'),
                   Item('tray', show_label=False, editor=EnumEditor(name='trays'))),
            UItem('canvas', editor=ComponentEditor())
        ),
                 buttons=['OK', 'Cancel'],
                 title='Edit Level',
                 resizable=True
        )
        return v

    def _trays_changed(self):
        self.tray = self.trays[0]

        #    def _tray_default(self):

#        return self.trays[0]
#============= EOF =============================================
