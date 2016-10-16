# ===============================================================================
# Copyright 2016 ross
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

from traits.api import HasTraits, Str, Float, Enum, Property, Bool
from traitsui.api import View, Item, EnumEditor

from pychron.pipeline.editors.yield_editor import YieldEditor
from pychron.pipeline.nodes.base import BaseNode
from pychron.pychron_constants import ARGON_KEYS


class YieldOptions(HasTraits):
    standard_ratio = Float(295.5)
    numerator = Enum(ARGON_KEYS)
    denominator = Str('Ar36')
    denominators = Property(depends_on='numerator')

    use_weighted_mean = Bool(True)
    @property
    def ratio_str(self):
        return '{}/{}'.format(self.numerator, self.denominator)

    def _get_denominators(self):
        return [a for a in ARGON_KEYS if a != self.numerator]

    def traits_view(self):
        v = View(Item('standard_ratio', label='Standard'),
                 Item('numerator'),
                 Item('denominator', editor=EnumEditor(name='denominators')),
                 buttons=['OK','Cancel'],
                 title='Yield Options')
        return v


class YieldNode(BaseNode):
    name = 'Detector Yield'
    options_klass = YieldOptions

    def run(self, state):
        if state.unknowns:
            editor = YieldEditor(analyses=state.unknowns,
                                 standard_ratio=self.options.standard_ratio,
                                 use_weighted_mean=self.options.use_weighted_mean,
                                 options=self.options)
            editor.initialize()
            state.editors.append(editor)
            self.editor = editor

# ============= EOF =============================================
