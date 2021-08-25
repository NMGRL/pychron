# ===============================================================================
# Copyright 2021 ross
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
from traits.api import Button, Any, Instance, Str, List, Bool
from traitsui.api import HGroup, View, VGroup, UItem, UCustom, Item, EnumEditor

from pychron.envisage.icon_button_editor import icon_button_editor
from pychron.envisage.tasks.base_editor import BaseTraitsEditor
from pychron.processing.analyses.view.analysis_view import AnalysisView


class RecentRunsEditor(BaseTraitsEditor):
    forward_button = Button
    back_button = Button
    analysis_view = Instance(AnalysisView, ())
    dvc = Instance('pychron.dvc.dvc.DVC')
    spectrometer = Str
    available_spectrometers = List
    stack = None
    stack_pointer = None
    stack_hash = None
    quick_load = Bool(True)

    def initialize(self):
        dvc = self.dvc
        specs = dvc.get_active_mass_spectrometer_names()
        self.available_spectrometers = specs
        self.stack = []
        self.stack_hash = set()

    def _spectrometer_changed(self):
        self._load_active_analysis()

    def _load_active_analysis(self):
        dvc = self.dvc
        ans = dvc.get_last_n_analyses(20, mass_spectrometer=self.spectrometer)
        if ans:
            ans = dvc.make_analyses(ans)
            ans = ans[::-1]
            self.stack = ans
            for a in ans:
                self.stack_hash.add(a.uuid)

            an = ans[-1]
            self.stack_pointer = len(ans)-1
            self.analysis_view.load(an, quick=self.quick_load)

    def _activate_analysis(self, an):
        self.analysis_view.load(an, quick=self.quick_load)

        if an.uuid not in self.stack_hash:
            self.stack.insert(0, an)
            self.stack_hash.add(an.uuid)

    def _back_button_fired(self):
        an = None
        if self.stack_pointer:
            self.stack_pointer -= 1
            an = self.stack[self.stack_pointer]

        if not an:
            ts = self.analysis_view.model.rundate
            uuid = self.analysis_view.model.uuid
            an = self.dvc.get_adjacent_analysis(uuid, ts, self.spectrometer, True)

        if an:
            self._activate_analysis(an)

    def _forward_button_fired(self):
        an = None
        if self.stack:
            if self.stack_pointer is None:
                self.stack_pointer = 0

            try:
                self.stack_pointer += 1
                an = self.stack[self.stack_pointer]
            except IndexError:
                pass

        if not an:
            ts = self.analysis_view.model.rundate
            uuid = self.analysis_view.model.uuid
            an = self.dvc.get_adjacent_analysis(uuid, ts, self.spectrometer, False)

        if an:
            self.analysis_view.load(an, quick=True)

    def traits_view(self):
        tgrp = HGroup(icon_button_editor('back_button', 'arrow_left'),
                      icon_button_editor('forward_button', 'arrow_right'),
                      Item('quick_load', tooltip='If checked only load the Main and Isotope views'),
                      Item('spectrometer', editor=EnumEditor(name='available_spectrometers')))

        agrp = UCustom('analysis_view')
        v = View(VGroup(tgrp, agrp))
        return v

# ============= EOF =============================================
