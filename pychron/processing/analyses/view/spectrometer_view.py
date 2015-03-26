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
from traits.api import HasTraits, Str, Int, Bool, Any, Float, Property, on_trait_change
from traitsui.api import View, UItem, Item, HGroup, VGroup, TabularEditor, Group
# ============= standard library imports ========================
# ============= local library imports  ==========================
from traitsui.tabular_adapter import TabularAdapter
from pychron.core.helpers.formatting import floatfmt


class DictTabularAdapter(TabularAdapter):
    columns = [('', 'key'), ('Value', 'value')]
    key_width = Int(200)
    value_text = Property

    def _get_value_text(self):
        try:
            return floatfmt(self.item.value)
        except:
            return 'Not Recorded'

class Value(HasTraits):
    name = Str
    value = Any


class SpectrometerView(HasTraits):
    model = Any
    name = 'Spectrometer'

    def __init__(self, an, *args, **kw):
        super(SpectrometerView, self).__init__(*args, **kw)
        self.model = an

    def trait_context(self):
        return {'object': self.model}

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
        v = View(VGroup(g1, g2))
        return v


# ============= EOF =============================================



