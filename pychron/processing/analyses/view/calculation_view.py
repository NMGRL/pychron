# ===============================================================================
# Copyright 2014 Jake Ross
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
from uncertainties import nominal_value

from pychron.core.helpers.formatting import floatfmt
from pychron.core.ui import set_qt
from pychron.pychron_constants import ARGON_KEYS


set_qt()

# ============= enthought library imports =======================
from traits.api import HasTraits, Str
from traitsui.api import View, UItem
# ============= standard library imports ========================
#============= local library imports  ==========================
from pychron.core.ui.text_editor import myTextEditor


class CalculationView(HasTraits):
    text = Str

    def load_view(self, a):
        lines = []

        lines.append(a.record_id)
        lines.append('age={}'.format(a.uage))
        isos = a.isotopes
        for isok in ARGON_KEYS:
            iso = isos[isok]

            vs = map(floatfmt, (isok, iso.value, iso.blank.value, iso.baseline.value))
            lines.append('{} = {} - {} - {}'.format(*vs))

        lines.append(' ')
        lines.append('Ar40* = Ar40 - Ar40atm - K40')

        vs = map(floatfmt, map(nominal_value, (a.corrected_intensities['Ar40'],
                                               a.computed['atm40'],
                                               a.non_ar_isotopes['k40'])))
        lines.append('Ar40* = {} - {} - {}'.format(*vs))

        self.text = '\n'.join(lines)

    def traits_view(self):
        editor = myTextEditor(bgcolor='#F7F6D0',
                              fontsize=10,
                              wrap=False,
                              tab_width=15)
        v = View(UItem('text', style='custom', editor=editor),
                 width=500,
                 resizable=True)
        return v


if __name__ == '__main__':
    from pychron.database.test_database import get_test_analysis

    a, man = get_test_analysis()
    cv = CalculationView()
    cv.load_view(a)
    cv.configure_traits()

# ============= EOF =============================================



