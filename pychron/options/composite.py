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
from traits.api import Instance, on_trait_change, Enum
from traits.trait_errors import TraitError

from pychron.options.group.spectrum_group_options import SpectrumGroupOptions
from pychron.options.isochron import InverseIsochronOptions
from pychron.options.options import FigureOptions
from pychron.options.spectrum import SpectrumOptions
from pychron.options.views.composite_views import VIEWS
from pychron.pychron_constants import MAIN


class CompositeOptions(FigureOptions):
    spectrum_options = Instance(SpectrumOptions)
    isochron_options = Instance(InverseIsochronOptions)
    use_plotting = True
    orientation_layout = Enum("Horizontal", "Vertical")
    group_options_klass = SpectrumGroupOptions

    def _get_state_hook(self, state):
        state["spectrum_options"] = self.spectrum_options.make_state()
        state["isochron_options"] = self.isochron_options.make_state()

    def _load_state_hook(self, state):
        so = state.pop("isochron_options")
        if so:
            try:
                self.isochron_options = InverseIsochronOptions()
                self.isochron_options.load(so)
            except TraitError as e:
                print("iso", e)

        so = state.pop("spectrum_options")
        if so:
            try:
                self.spectrum_options = SpectrumOptions()
                self.spectrum_options.load(so)
            except TraitError as e:
                print("spec", e)

    def setup(self):
        super(CompositeOptions, self).setup()
        if not self.spectrum_options:
            self.spectrum_options = SpectrumOptions()
        if not self.isochron_options:
            self.isochron_options = InverseIsochronOptions()

        self.spectrum_options.setup()
        self.isochron_options.setup()

    @on_trait_change("groups[]")
    def handle_group_change(self):
        self.spectrum_options.groups = self.groups
        self.isochron_options.groups = self.groups

    @on_trait_change("spectrum_options:[bgcolor,plot_bgcolor]")
    def handle(self, obj, name, old, new):
        self.isochron_options.trait_set(**{name: new})

    def get_subview(self, name):
        name = name.lower()

        klass = self._get_subview(name)

        if name in (
            MAIN.lower(),
            "spectrum",
            "appearance(spec.)",
            "display(spec.)",
            "calculations(spec.)",
        ):
            obj = klass(model=self.spectrum_options)
        elif name in ("isochron", "calculations(iso.)", "appearance(iso.)"):
            obj = klass(model=self.isochron_options)
        else:
            obj = klass(model=self)

        return obj

    def initialize(self):
        self.subview_names = [
            "Spectrum",
            "Appearance(Spec.)",
            "Display(Spec.)",
            "Calculations(Spec.)",
            "Isochron",
            "Calculations(Iso.)",
            "Appearance(Iso.)",
            "Layout",
            "Title",
            "Groups",
        ]

    def _get_subview(self, name):
        return VIEWS[name]


# ============= EOF =============================================
