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



#============= enthought library imports =======================
from chaco.api import AbstractOverlay

#============= standard library imports ========================

#============= local library imports  ==========================


class BorderOverlay(AbstractOverlay):
    def overlay(self, component, gc, view_bounds=None, mode='normal'):
        '''
            
        '''
#        print component.outer_bounds, component.outer_position
        gc.set_stroke_color((0, 1, 0))
        x, y = component.outer_position
        w, h = component.outer_bounds
        gc.rect(x - 3, y - 3, w + 6, h + 6)

        gc.stroke_path()
#============= views ===================================
#============= EOF ====================================
