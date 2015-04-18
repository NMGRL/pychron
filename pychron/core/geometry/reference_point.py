# ===============================================================================
# Copyright 2012 Jake Ross
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
from traits.api import HasTraits, Float, String, List, Property, Str
from traitsui.api import View, HGroup, Item
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.core.ui.custom_label_editor import CustomLabel

HELP_TAG_POINT = '''Enter the x, y for this point {:0.3f},{:0.3f}
in data space i.e mm
'''

HELP_TAG_HOLE = '''Enter the hole for this point {:0.3f},{:0.3f}'''


class ReferencePoint(HasTraits):
    x = Float
    y = Float
    help_tag = String(HELP_TAG_POINT)

    def __init__(self, pt, *args, **kw):
        self.help_tag = self.help_tag.format(*pt)
        super(ReferencePoint, self).__init__(*args, **kw)

    def traits_view(self):
        v = View(CustomLabel('help_tag',
                             top_padding=10,
                             left_padding=10,
                             color='maroon'),
                 HGroup('x', 'y'),
                 buttons=['OK', 'Cancel'],
                 kind='modal',
                 title='Reference Point')
        return v


class ReferenceHole(ReferencePoint):
    hole = Property
    _hole = Str
    help_tag = String(HELP_TAG_HOLE)
    valid_holes = List

    def _get_hole(self):
        return self._hole

    def _set_hole(self, v):
        self._hole = v

    def _validate_hole(self, v):
        if v in self.valid_holes:
            return v

    def traits_view(self):
        v = View(
            CustomLabel('help_tag',
                        top_padding=10,
                        left_padding=10,
                        color='maroon'),
            Item('hole'),
            buttons=['OK', 'Cancel'],
            kind='modal',
            title='Reference Hole')
        return v

# ============= EOF =============================================
