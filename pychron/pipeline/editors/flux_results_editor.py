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
from traits.api import HasTraits, Str, Int, Bool, Float, Property, List
from traitsui.api import View, UItem, TableEditor
from traitsui.extras.checkbox_column import CheckboxColumn
from traitsui.table_column import ObjectColumn
# ============= standard library imports ========================
# ============= local library imports  ==========================
from uncertainties import nominal_value
from uncertainties import std_dev
from pychron.core.helpers.formatting import calc_percent_error, floatfmt
from pychron.envisage.tasks.base_editor import BaseTraitsEditor


class FluxPosition(HasTraits):
    hole_id = Int
    identifier = Str
    sample = Str
    x = Float
    y = Float
    z = Float
    theta = Float
    saved_j = Float
    saved_jerr = Float

    mean_j = Float
    mean_jerr = Float

    n = Int

    j = Float(enter_set=True, auto_set=False)
    jerr = Float(enter_set=True, auto_set=False)
    use = Bool(True)
    save = Bool(False)
    dev = Float

    percent_saved_error = Property
    percent_mean_error = Property
    percent_pred_error = Property

    def _get_percent_saved_error(self):
        return calc_percent_error(self.saved_j, self.saved_jerr)

    def _get_percent_mean_error(self):
        if self.mean_jerr and self.mean_jerr:
            return calc_percent_error(self.mean_j, self.mean_jerr)

    def _get_percent_pred_error(self):
        if self.j and self.jerr:
            return calc_percent_error(self.j, self.jerr)


class FluxResultsEditor(BaseTraitsEditor):
    positions = List

    def add_position(self, identifier, irradiation_position, sample, sj, mj, n):
        f = FluxPosition(identifier=identifier,
                         sample=sample,
                         hole_id=irradiation_position,
                         mean_j=nominal_value(mj),
                         mean_jerr=std_dev(mj),
                         saved_j=nominal_value(sj),
                         saved_jerr=std_dev(sj),
                         n=n)

        self.positions.append(f)

    def traits_view(self):
        def column(klass=ObjectColumn, editable=False, **kw):
            return klass(text_font='arial 10', editable=editable, **kw)

        cols = [
            column(klass=CheckboxColumn, name='use', label='Use', editable=True, width=30),
            column(name='hole_id', label='Hole'),
            column(name='identifier', label='Identifier'),
            column(name='sample', label='Sample', width=115),

            # column(name='x', label='X', format='%0.3f', width=50),
            # column(name='y', label='Y', format='%0.3f', width=50),
            # column(name='theta', label=u'\u03b8', format='%0.3f', width=50),

            column(name='n', label='N'),
            column(name='saved_j', label='Saved J',
                   format_func=lambda x: floatfmt(x, n=6, s=4)),
            column(name='saved_jerr', label=u'\u00b1\u03c3',
                   format_func=lambda x: floatfmt(x, n=6, s=4)),
            column(name='percent_saved_error',
                   label='%',
                   format_func=lambda x: floatfmt(x, n=2)),
            column(name='mean_j', label='Mean J',
                   format_func=lambda x: floatfmt(x, n=6, s=4) if x else ''),
            column(name='mean_jerr', label=u'\u00b1\u03c3',
                   format_func=lambda x: floatfmt(x, n=6, s=4) if x else ''),
            column(name='percent_mean_error',
                   label='%',
                   format_func=lambda x: floatfmt(x, n=2) if x else ''),
            column(name='j', label='Pred. J',
                   format_func=lambda x: floatfmt(x, n=8, s=4),
                   width=75),
            column(name='jerr',
                   format_func=lambda x: floatfmt(x, n=10, s=4),
                   label=u'\u00b1\u03c3',
                   width=75),
            column(name='percent_pred_error',
                   label='%',
                   format_func=lambda x: floatfmt(x, n=2) if x else ''),
            column(name='dev', label='dev',
                   format='%0.2f',
                   width=70),
            column(klass=CheckboxColumn, name='save', label='Save', editable=True, width=30)]

        editor = TableEditor(columns=cols, sortable=False,
                             reorderable=False)

        pgrp = UItem('positions', editor=editor)
        v = View(pgrp)
        return v

# ============= EOF =============================================
