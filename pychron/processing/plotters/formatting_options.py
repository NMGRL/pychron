# ===============================================================================
# Copyright 2015 Jake Ross
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

# ============= enthought library imports =======================
from traits.api import HasTraits, Str, Int, Color
# ============= standard library imports ========================
import os
import yaml
# ============= local library imports  ==========================


class FormattingOptions(HasTraits):
    x_title_font = Str
    x_tick_label_font = Str
    x_tick_in = Int
    x_tick_out = Int

    y_title_font = Str
    y_tick_label_font = Str
    y_tick_in = Int
    y_tick_out = Int

    bgcolor = Color
    plot_bgcolor = Color

    label_font = Str

    def __init__(self, path, *args, **kw):
        super(FormattingOptions, self).__init__(*args, **kw)
        self._load(path)

    def _load(self, p):
        # print 'ff', p, os.path.isfile(p)
        if os.path.isfile(p):
            with open(p, 'r') as rfile:
                yd = yaml.load(rfile)
                # print p, yd
                self.trait_set(**yd)

    def get_value(self, axis, attr):
        """
        get the attribute value for an axis and attr

        :param axis: 'x' or 'y'
        :param attr: attribute name
        :type attr: str
        :return: str, int, float
        """
        value = getattr(self, '{}_{}'.format(axis, attr))

        return value



# ============= EOF =============================================



