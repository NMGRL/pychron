# ===============================================================================
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
# ===============================================================================

# ============= enthought library imports =======================
from traits.api import HasTraits, Str, Float, Bool, Int, Property, CStr
from traitsui.tabular_adapter import TabularAdapter

from pychron.pychron_constants import PLUSMINUS


# ============= standard library imports ========================
# ============= local library imports  ==========================
class BaseIrradiatedPosition(HasTraits):
    identifier = Str
    material = Str
    sample = Str
    grainsize = Str
    hole = Int
    alt_hole = Int
    project = Str
    principal_investigator = Str

    j = Float(0)
    j_err = Float(0)
    pred_j = Float
    pred_j_err = Float
    x = Float
    y = Float
    residual = Property(depends_on='j,pred_j')

    use = Bool
    save = Bool

    def __init__(self, pos=None, *args, **kw):
        super(BaseIrradiatedPosition, self).__init__(*args, **kw)
        if pos is not None:
            self.x, self.y = pos

    def _get_residual(self):
        pe = 0
        if self.pred_j:
            try:
                pe = abs(self.j - self.pred_j) / self.j * 100
            except ZeroDivisionError:
                pe = 0
        return pe


class IrradiatedPosition(BaseIrradiatedPosition):
    size = Str
    weight = CStr
    note = Str
    analyzed = Bool


class BaseIrradiatedPositionAdapter(TabularAdapter):
    columns = [
        ('Hole', 'hole'),
        ('Alt. Hole', 'alt_hole'),
        ('Labnumber', 'labnumber'),
        ('Sample', 'sample'),
        ('Project', 'project'),
        ('J', 'j'),
        (u'{}J'.format(PLUSMINUS), 'j_err'),
        ('Note', 'note')]

    hole_width = Int(45)


class IrradiatedPositionAdapter(TabularAdapter):
    columns = [
        ('Hole', 'hole'),
        ('Identifier', 'identifier'),
        ('Sample', 'sample'),
        ('PI', 'principal_investigator'),
        ('Project', 'project'),
        ('Material', 'material'),
        ('Grainsize', 'grainsize'),
        #               ('Size', 'size'),
        ('Weight', 'weight'),
        ('J', 'j'),
        (u'{}J'.format(PLUSMINUS), 'j_err'),
        ('Note', 'note')]

    identifier_width = Int(80)
    hole_width = Int(50)
    sample_width = Int(100)
    project_width = Int(150)
    material_width = Int(100)
    grainsize_width = Int(70)
    size_width = Int(50)
    weight_width = Int(50)
    j_width = Int(75)
    j_err_width = Int(75)

    j_text = Property
    j_err_text = Property

    font = 'arial 10'

    #    hole_can_edit = False

    #    def _get_hole_width(self):
    #        return 35

    def _set_j_text(self, t):
        self.item.j = float(t)

    def _set_j_err_text(self, t):
        self.item.j_err = t

    def _get_j_text(self):
        return '{:0.6E}'.format(self.item.j)

    def _get_j_err_text(self):
        return '{:0.6E}'.format(self.item.j_err)

    def get_bg_color(self, obj, trait, row, column):
        item = getattr(obj, trait)[row]
        if item.analyzed:
            return '#B0C4DE'

# ============= EOF =============================================
