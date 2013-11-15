#===============================================================================
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
#===============================================================================



#=============enthought library imports=======================
from traits.api import HasTraits, Float, Enum, Bool, Int, Property
from traitsui.api import View, Item, Group, VGroup
#============= standard library imports ========================

#============= local library imports  ==========================


class FocusParameters(HasTraits):

    fstart = Float(20)
    fend = Float(10)
    step_scalar = Float(1)
#    style = Enum('laplace', '2step-laplace', '2step-sobel', 'var', 'sobel')
    operator = Enum('laplace', 'var', 'sobel')

#    discrete = Bool(False)

    negative_window = Float(3)
    positive_window = Float(1)

    velocity_scalar1 = Float(1)
    velocity_scalar2 = Float(1)

    crop_bind = Bool(True)
    crop_width = Property(depends_on='_crop_width')
    crop_height = Property(depends_on='_crop_height')
    _crop_width = Int(300)
    _crop_height = Int(300)

    zoom = Float(50)

    def _get_crop_width(self):
        return self._crop_width

    def _get_crop_height(self):
        return self._crop_height

    def _set_crop_width(self, v):
        self._crop_width = v
        if self.crop_bind:
            self._crop_height = v

    def _set_crop_height(self, v):
        self._crop_height = v
        if self.crop_bind:
            self._crop_width = v

    def _validate_crop_width(self, v):
        return self._validate_int(v)

    def _validate_crop_height(self, v):
        return self._validate_int(v)

    def _validate_int(self, v):
        try:
            v = int(v)
            return v
        except ValueError:
            pass

    def traits_view(self):
        v = View(
               Item('fstart'),
               Item('fend'),
               Item('operator'),
#               Item('discrete'),
               Item('step_scalar', visible_when='discrete'),
               Item('zoom'),
               Group(
                     Item('velocity_scalar1'),
                     Item('negative_window'),
                     Item('positive_window'),
                     Item('velocity_scalar2'),
                     VGroup(Item('crop_width'),
                            Item('crop_height'),
                            Item('crop_bind'))


#                     enabled_when='style=="2step"'
                     ),
               )
        return v

#============= EOF =====================================
