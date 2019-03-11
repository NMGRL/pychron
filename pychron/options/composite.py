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
from traits.api import Instance

from pychron.options.isochron import InverseIsochronOptions
from pychron.options.options import BaseOptions
from pychron.options.spectrum import SpectrumOptions
from pychron.options.views.composite_views import VIEWS


class CompositeOptions(BaseOptions):
    spectrum_options = Instance(SpectrumOptions, ())
    isochron_options = Instance(InverseIsochronOptions, ())
    use_plotting = True

    def setup(self):
        if not self.spectrum_options:
            self.spectrum_options = SpectrumOptions()
        if not self.isochron_options:
            self.isochron_options = InverseIsochronOptions()

        self.spectrum_options.setup()
        self.isochron_options.setup()

    def get_subview(self, name):
        name = name.lower()

        if name == 'main':
            try:
                klass = self._get_subview(name)
            except KeyError:
                klass = self._main_options_klass
        else:
            klass = self._get_subview(name)

        # if self.isochron_options is None:
        #     self.isochron_options = InverseIsochronOptions()
        # if self.spectrum_options is None:
        #     self.spectrum_options = SpectrumOptions()

        if name in ('main', 'main(spectrum)'):
            obj = klass(model=self.spectrum_options)
        elif name == 'main(isochron)':
            obj = klass(model=self.isochron_options)

        return obj

    def initialize(self):
        self.subview_names = ['Main(Spectrum)', 'Main(Isochron)']

    def _get_subview(self, name):
        return VIEWS[name]
# ============= EOF =============================================
