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

# ============= enthought library imports =======================

from pyface.tasks.traits_editor import TraitsEditor
from traits.api import Button, Instance, Int
from traitsui.api import (
    View,
    UItem,
    InstanceEditor,
    VGroup,
    HGroup,
    TabularEditor,
    VSplit,
)
from traitsui.tabular_adapter import TabularAdapter

from pychron.envisage.icon_button_editor import icon_button_editor


# ============= standard library imports ========================
# ============= local library imports  ==========================


class ScanEditor(TraitsEditor):
    id = "pychron.scan"
    model = Instance("pychron.spectrometer.scan_manager.ScanManager")

    def stop(self):
        self.model.stop()

    def traits_view(self):
        v = View(UItem("graph", style="custom", editor=InstanceEditor()))
        return v


class PeakCenterResultsAdapter(TabularAdapter):
    columns = [
        ("Detector", "detector"),
        ("Center DAC (V)", "center_dac"),
        ("Resolution", "resolution"),
        ("Low Mass Resolving Power", "low_resolving_power"),
        ("High Mass Resolving Power", "high_resolving_power"),
    ]

    detector_width = Int(100)
    center_dac_width = Int(150)
    resolution_width = Int(150)
    low_resolving_power_width = Int(150)


class PeakCenterEditor(ScanEditor):
    model = Instance("pychron.spectrometer.jobs.peak_center.PeakCenter")

    def traits_view(self):
        v = View(
            VSplit(
                UItem("graph", style="custom", height=0.8, editor=InstanceEditor()),
                UItem(
                    "results",
                    height=0.2,
                    editor=TabularEditor(adapter=PeakCenterResultsAdapter()),
                ),
            )
        )
        return v


class ScannerEditor(ScanEditor):
    model = Instance("pychron.spectrometer.jobs.base_scanner.BaseScanner")


class CoincidenceEditor(PeakCenterEditor):
    model = Instance("pychron.spectrometer.jobs.coincidence.Coincidence")
    stop_button = Button

    def _stop_button_fired(self):
        self.stop()

    def traits_view(self):
        tgrp = HGroup(
            icon_button_editor(
                "editor.stop_button", "stop", tooltip="Stop the current scan"
            )
        )
        v = View(VGroup(tgrp, UItem("graph", style="custom", editor=InstanceEditor())))
        return v


# ============= EOF =============================================
