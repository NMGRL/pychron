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
from traits.api import HasTraits, Int, List, Str, Bool
from traitsui.api import UItem, Item, VGroup, Controller, EnumEditor, CheckListEditor

from pychron.core.helpers.traitsui_shortcuts import okcancel_view
from pychron.persistence_loggable import PersistenceMixin
from pychron.pychron_constants import DEFAULT_MONITOR_NAME


def formatter(x):
    return x.lower().replace(" ", "_")


class FindReferencesConfigModel(HasTraits, PersistenceMixin):
    analysis_types = List
    threshold = Int
    mass_spectrometers = List
    available_mass_spectrometers = List
    extract_devices = List
    available_extract_devices = List
    available_irradiations = List
    irradiations = List
    monitor_sample = Str(DEFAULT_MONITOR_NAME)
    monitor_samples = List
    replace = Bool(False)
    pattributes = ("analysis_types", "threshold")

    persistence_name = "find_references_config"

    @property
    def formatted_analysis_types(self):
        return [formatter(a) for a in self.analysis_types]


class FindReferencesConfigView(Controller):
    def init(self, info):
        self.model.load()
        return True

    def closed(self, info, is_ok):
        if is_ok:
            self.model.dump()

    def traits_view(self):
        v = okcancel_view(
            VGroup(
                VGroup(
                    UItem(
                        "analysis_types",
                        style="custom",
                        editor=CheckListEditor(
                            values=[
                                "Blank Unknown",
                                "Blank Air",
                                "Blank Cocktail",
                                "Blank",
                                "Air",
                                "Cocktail",
                            ]
                        ),
                    ),
                    show_border=True,
                    label="Analysis Types",
                ),
                VGroup(
                    UItem(
                        "mass_spectrometers",
                        style="custom",
                        editor=CheckListEditor(name="available_mass_spectrometers"),
                    ),
                    show_border=True,
                    label="Mass Spectrometers",
                ),
                VGroup(
                    UItem(
                        "extract_devices",
                        style="custom",
                        editor=CheckListEditor(name="available_extract_devices"),
                    ),
                    show_border=True,
                    label="Extract Devices",
                ),
                VGroup(
                    UItem(
                        "irradiations",
                        style="custom",
                        editor=CheckListEditor(name="available_irradiations"),
                    ),
                    Item("monitor_sample", editor=EnumEditor(name="monitor_samples")),
                    show_border=True,
                    label="Monitors",
                ),
                Item(
                    "replace",
                    label="Replace analyses used to find the references with the references",
                ),
                Item("threshold", label="Threshold (hrs)"),
            ),
            title="Configure Find References",
        )

        return v


# ============= EOF =============================================
