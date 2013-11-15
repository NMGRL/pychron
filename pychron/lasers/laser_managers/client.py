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
from traits.api import HasTraits, Any, Str, Range, Property, cached_property, \
    on_trait_change, String, Either, Float, Event, Bool, Enum, Int
from traitsui.api import View, Item, EnumEditor, HGroup, UItem

#============= standard library imports ========================
import os
from threading import Thread
#============= local library imports  ==========================
from pychron.envisage.tasks.pane_helpers import icon_button_editor
from pychron.paths import paths


class LaserClient(HasTraits):
    parent = Any


class LaserControlsClient(LaserClient):
    pass


class LaserOpticsClient(LaserClient):
    pass


class UVLaserControlsClient(LaserControlsClient):
    fire = Event
    stop = Event
    #fire_label = Property(depends_on='firing')
    firing = Bool
    fire_mode = Enum('Burst', 'Continuous')
    nburst = Property(Int, depends_on='_nburst')
    _nburst = Int

    def traits_view(self):
        v = View(HGroup(
            icon_button_editor('fire', 'lightning',
                               enabled_when='not firing',
                               editor_kw={'label_value': 'fire_label'}),
            icon_button_editor('stop', 'stop',
                               enabled_when='firing',
                               editor_kw={'label_value': 'fire_label'}),
            UItem('fire_mode')),
                 Item('nburst'),
        )

        return v

    def _get_nburst(self):
        return self._nburst

    def _set_nburst(self, v):
        self._nburst = v

    def _fire_fired(self):
        pass
        self.firing = True

    def _stop_fired(self):
        self.firing = False


class UVLaserOpticsClient(LaserOpticsClient):
    mask = Property(String(enter_set=True, auto_set=False),
                    depends_on='_mask')
    _mask = Either(Str, Float)

    masks = Property
    attenuator = String(enter_set=True, auto_set=False)
    #attenuators = Property
    zoom = Range(0.0, 100.0)

    @on_trait_change('mask, attenuator, zoom')
    def _motor_changed(self, name, new):
        if new is not None:
            t = Thread(target=self.parent.set_motor, args=(name, new))
            t.start()

    def _set_mask(self, m):
        self._mask = m

    def _get_mask(self):
        return self._mask

    def _validate_mask(self, m):
        if m in self.masks:
            return m
        else:
            try:
                return float(m)
            except ValueError:
                pass

    def traits_view(self):
        v = View(
            HGroup(Item('mask', editor=EnumEditor(name='masks')),
                   UItem('mask')),
            Item('attenuator'),
        )

        return v

    @cached_property
    def _get_masks(self):
        return self._get_motor_values('mask_names')

    #@cached_property
    #def _get_attenuators(self):
    #    return self._get_motor_values('attenuators')

    def _get_motor_values(self, name):
        p = os.path.join(paths.device_dir, 'fusions_uv', '{}.txt'.format(name))
        values = []
        if os.path.isfile(p):
            with open(p, 'r') as fp:
                for lin in fp:
                    lin = lin.strip()
                    if not lin or lin.startswith('#'):
                        continue
                    values.append(lin)

        return values

#============= EOF =============================================
