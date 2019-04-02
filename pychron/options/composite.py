# ===============================================================================
# Copyright 2019 ross
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
from traits.api import Instance, on_trait_change

from pychron.options.isochron import InverseIsochronOptions
from pychron.options.options import FigureOptions
from pychron.options.spectrum import SpectrumOptions
from pychron.options.views.composite_views import VIEWS
from pychron.pychron_constants import MAIN


class CompositeOptions(FigureOptions):
    spectrum_options = Instance(SpectrumOptions)
    isochron_options = Instance(InverseIsochronOptions)
    use_plotting = True

    def setup(self):
        if not self.spectrum_options:
            self.spectrum_options = SpectrumOptions()
        if not self.isochron_options:
            self.isochron_options = InverseIsochronOptions()

        self.spectrum_options.setup()
        self.isochron_options.setup()

    @on_trait_change('spectrum_options:[bgcolor,plot_bgcolor]')
    def handle(self, obj, name, old, new):
        self.isochron_options.trait_set(**{name: new})

    def get_subview(self, name):
        name = name.lower()

        klass = self._get_subview(name)

        if name in (MAIN.lower(), 'spectrum', 'appearance(spec.)', 'display(spec.)', 'calculations(spec.)'):
            obj = klass(model=self.spectrum_options)
        elif name in ('isochron', 'appearance(iso.)'):
            obj = klass(model=self.isochron_options)

        return obj

    def initialize(self):
        self.subview_names = ['Spectrum',
                              'Appearance(Spec.)',
                              'Display(Spec.)',
                              'Calculations(Spec.)',

                              'Isochron',
                              'Appearance(Iso.)',
                              ]

    def _get_subview(self, name):
        return VIEWS[name]
# ============= EOF =============================================
