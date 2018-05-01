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
from __future__ import absolute_import
from traits.api import HasTraits, Str, Int, Any, Property, List
from traitsui.api import View, UItem, VGroup, TabularEditor, Group, HGroup
# ============= standard library imports ========================
# ============= local library imports  ==========================
from traitsui.tabular_adapter import TabularAdapter
from pychron.core.helpers.formatting import floatfmt
from pychron.core.helpers.isotope_utils import sort_detectors


class DictTabularAdapter(TabularAdapter):
    columns = [('', 'key'), ('Value', 'value')]
    key_width = Int(100)
    value_text = Property

    def _get_value_text(self):
        try:
            return floatfmt(float(self.item.value))
        except (ValueError, TypeError):
            return 'NaN'


class DValue(HasTraits):
    key = Str
    value = Any

    def __init__(self, key, value):
        self.key = key
        self.value = value


class SpectrometerView(HasTraits):
    # model = Any
    name = 'Spectrometer'
    source_parameters = List
    deflections = List
    gains = List

    def __init__(self, an, *args, **kw):
        super(SpectrometerView, self).__init__(*args, **kw)

        # source
        sp = an.source_parameters
        sd = [DValue(k, v) for k, v in sp.items()]
        self.source_parameters = sd

        # deflections
        defls = an.deflections
        names = sort_detectors(list(defls.keys()))
        ds = [DValue(ni, defls[ni]) for ni in names]
        self.deflections = ds

        # gains
        gains = an.gains
        gs = [DValue(ni, gains.get(ni, 0)) for ni in names]
        self.gains = gs

    def traits_view(self):
        g1 = Group(UItem('source_parameters',
                         editor=TabularEditor(adapter=DictTabularAdapter(),
                                              editable=False)),
                   show_border=True,
                   label='Source')

        g2 = Group(UItem('deflections',
                         editor=TabularEditor(adapter=DictTabularAdapter(),
                                              editable=False)),
                   show_border=True,
                   label='Deflections')

        g3 = Group(UItem('gains',
                         editor=TabularEditor(adapter=DictTabularAdapter(),
                                              editable=False)),
                   show_border=True,
                   label='Gains')
        v = View(HGroup(g1, g2, g3))
        return v

# ============= EOF =============================================
