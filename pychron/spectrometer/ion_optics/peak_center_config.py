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
import os
import pickle

# from apptools import sweet_pickle as pickle
from traits.api import HasTraits, Str, Bool, Float, Either, List, Enum, Int, Any, Button
from traitsui.api import View, Item, HGroup, EnumEditor, UItem, VGroup, InstanceEditor

from pychron.core.helpers.filetools import add_extension, glob_list_directory
from pychron.core.helpers.traitsui_shortcuts import okcancel_view
from pychron.core.ui.check_list_editor import CheckListEditor
from pychron.envisage.icon_button_editor import icon_button_editor
from pychron.paths import paths
from pychron.saveable import SaveButton, Saveable, SaveableHandler


class PeakCenterConfigHandler(SaveableHandler):
    def save(self, info):
        info.object.save()
        self.close(info, True)

    def closed(self, info, isok):
        if isok:
            info.object.dump()
        return isok


class PeakCenterConfig(HasTraits):
    name = Str

    detectors = List(transient=True)
    detector = Str
    # detector_name = Str

    additional_detectors = List
    available_detectors = List

    isotope = Str("Ar40")
    isotopes = List(transient=True)
    dac = Float
    use_current_dac = Bool(True)
    # integration_time = Enum(QTEGRA_INTEGRATION_TIMES)
    integration_time = Either(Float, Int)
    integration_times = List(transient=True)

    # directions = Enum('Increase', 'Decrease', 'Oscillate')
    directions = Enum("Increase", "Decrease")

    dataspace = Enum("dac", "mass", "av")

    window = Float(0.015)
    step_width = Float(0.0005)
    min_peak_height = Float(1.0)
    percent = Int(80)

    use_interpolation = Bool
    interpolation_kind = Enum(
        "linear", "nearest", "zero", "slinear", "quadratic", "cubic"
    )
    n_peaks = Enum(1, 2, 3, 4)
    select_n_peak = Int
    select_n_peaks = List

    use_dac_offset = Bool
    dac_offset = Float
    calculate_all_peaks = Bool
    use_mftable_dac = Bool

    update_others = Bool(True)

    use_extend = Bool(False)

    # def _integration_time_default(self):
    #     return QTEGRA_INTEGRATION_TIMES[4]  # 1.048576

    def _n_peaks_changed(self, new):
        self.select_n_peaks = [i + 1 for i in range(new)]

        if self.select_n_peak > new:
            self.select_n_peak = new

    def _detector_changed(self, new):
        if new:
            self.available_detectors = [d for d in self.detectors if d != new]

    def mftable_view(self):
        m_grp = self._get_measure_grp()
        pp_grp = self._get_post_process_grp(include_update_others=False)

        v = View(VGroup(m_grp, pp_grp))
        return v

    def traits_view(self):
        degrp = self._get_additional_detectors_grp()

        m_grp = self._get_measure_grp()
        pp_grp = self._get_post_process_grp()

        v = View(
            VGroup(
                HGroup(
                    Item("detector", editor=EnumEditor(name="detectors")),
                    Item("isotope", editor=EnumEditor(name="isotopes")),
                ),
                degrp,
                m_grp,
                pp_grp,
            ),
            resizable=True,
        )
        return v

    def _get_post_process_grp(self, include_update_others=True):
        pp_grp = VGroup(
            Item("min_peak_height", label="Min Peak Height (fA)"),
            Item("percent", label="% Peak Height"),
            HGroup(
                Item("use_interpolation", label="Use Interpolation"),
                UItem("interpolation_kind", enabled_when="use_interpolation"),
            ),
            Item("n_peaks", label="Deconvolve N. Peaks"),
            Item(
                "select_n_peak",
                editor=EnumEditor(name="select_n_peaks"),
                enabled_when="n_peaks>1",
                label="Select Peak",
            ),
            HGroup(
                Item("use_dac_offset", label="DAC Offset"),
                UItem("dac_offset", enabled_when="use_dac_offset"),
            ),
            Item("calculate_all_peaks"),
            show_border=True,
            label="Post Process",
        )

        if include_update_others:
            itm = Item(
                "update_others",
                label="Update All Detectors",
                tooltip="Update all the detectors in the "
                "mftable not only the reference "
                "detector",
            )
            pp_grp.content.append(itm)
        return pp_grp

    def _get_measure_grp(self):
        mass_grp = VGroup(
            HGroup(
                Item("use_current_dac", label="Use Current DAC"),
                Item("use_mftable_dac", label="Use DAC from MFTable"),
            ),
            Item(
                "dac",
                label="Center DAC",
                enabled_when="not use_current_dac and not use_mftable_dac",
            ),
            visible_when='dataspace=="dac"',
        )

        dac_grp = VGroup(
            HGroup(
                Item("use_current_dac", label="Use Current Mass"),
                Item("use_mftable_dac", label="Use Mass from MFTable"),
            ),
            Item(
                "dac",
                label="Center Mass",
                enabled_when="not use_current_dac and not use_mftable_dac",
            ),
            visible_when='dataspace=="mass"',
        )

        center_grp = VGroup(mass_grp, dac_grp, show_border=True, label="Center")
        """dac_grp = VGroup(HGroup(Item('use_current_dac',
                                     label='Use Current DAC',
                                    visible_when='dataspace=="dac"'),
                                Item('use_mftable_dac',
                                     label='Use DAC from MFTable',
                                     visible_when='dataspace=="dac"'),
                                
                                Item('use_current_dac',
                                    label='Use Current Mass',
                                    visible_when='dataspace=="mass"'),
                                Item('use_mftable_dac', label='Use Mass from MFTable'),
                                     visible_when='dataspace=="mass"'),
                         
                         Item('dac', label='Center DAC', enabled_when='not use_current_dac and not use_mftable_dac',
                         visible_when='dataspace=="dac"'),
                         Item('dac', label='Center Mass', enabled_when='not use_current_dac and not use_mftable_dac',
                         visible_when='dataspace=="mass"'),
                        )"""

        dataspace_grp = HGroup(UItem("dataspace"), label="Dataspace", show_border=True)

        m_grp = VGroup(
            dataspace_grp,
            center_grp,
            Item("integration_time", editor=EnumEditor(name="integration_times")),
            Item("directions"),
            Item("window", visible_when='dataspace=="av"', label="Peak Width (V)"),
            Item("step_width", visible_when='dataspace=="av"', label="Step Width (V)"),
            Item("window", visible_when='dataspace=="dac"', label="Peak Width (V)"),
            Item("step_width", visible_when='dataspace=="dac"', label="Step Width (V)"),
            Item("window", visible_when='dataspace=="mass"', label="Peak Width (amu)"),
            Item(
                "step_width", visible_when='dataspace=="mass"', label="Step Width (amu)"
            ),
            Item("use_extend"),
            show_border=True,
            label="Measure",
        )
        return m_grp

    def _get_additional_detectors_grp(self):
        degrp = VGroup(
            UItem(
                "additional_detectors",
                style="custom",
                editor=CheckListEditor(
                    name="available_detectors",
                    capitalize=False,
                    cols=max(1, len(self.available_detectors)),
                ),
            ),
            show_border=True,
            label="Additional Detectors",
        )
        return degrp

    @property
    def use_accel_voltage(self):
        return self.dataspace == "av"

    @property
    def active_detectors(self):
        return [self.detector] + self.additional_detectors


class ItemConfigurer(Saveable):
    active_item = Any

    active_name = Str
    names = List

    item_klass = None

    new_name = Str
    add_button = Button
    root = Str
    save_enabled = True
    view_name = Str

    def dump(self):
        p = os.path.join(paths.hidden_dir, add_extension("config", ".p"))
        with open(p, "wb") as wfile:
            obj = {"name": self.active_name}
            pickle.dump(obj, wfile)

        self.dump_item(self.active_item)

    def save(self):
        self.dump()

    def load(self, **kw):
        names = glob_list_directory(self.root, remove_extension=True, extension=".p")
        if "Default" not in names:
            item = self.item_klass()
            item.name = "Default"
            self.dump_item(item)
            names = glob_list_directory(
                self.root, remove_extension=True, extension=".p"
            )

        name = "Default"
        p = os.path.join(paths.hidden_dir, add_extension("config", ".p"))
        if os.path.isfile(p):
            with open(p, "rb") as rfile:
                obj = pickle.load(rfile)
                name = obj.get("name", "Default")

        self.names = names
        self.active_name = name

        self.active_item.trait_set(**kw)

    def dump_item(self, item):
        name = item.name
        if not name:
            name = "Default"

        p = os.path.join(self.root, add_extension(name, ".p"))
        with open(p, "wb") as wfile:
            pickle.dump(item, wfile)

    def get(self, name):
        p = os.path.join(self.root, add_extension(name, ".p"))
        if os.path.isfile(p):
            try:
                with open(p, "rb") as rfile:
                    obj = pickle.load(rfile, encoding="latin1")
            except BaseException as e:
                obj = self.item_klass()

        else:
            obj = self.item_klass()

        return obj

    def _load_names(self):
        names = glob_list_directory(self.root, remove_extension=True, extension=".p")
        self.names = names

    def _active_name_changed(self, name):
        if name:
            self.active_item = self.get(name)

    def _add_button_fired(self):
        v = okcancel_view(UItem("new_name"), width=300, title="New Configuration Name")
        info = self.edit_traits(view=v)
        if info.result:
            obj = self.active_item
            obj.name = self.new_name
            self.dump_item(obj)
            self._load_names()
            self.active_name = self.new_name

    def traits_view(self):
        v = View(
            VGroup(
                HGroup(
                    UItem("active_name", width=200, editor=EnumEditor(name="names")),
                    icon_button_editor("add_button", "add"),
                ),
                UItem("_"),
                UItem(
                    "active_item",
                    style="custom",
                    editor=InstanceEditor(view=self.view_name),
                ),
                UItem("_"),
            ),
            buttons=["OK", "Cancel", SaveButton],
            kind="livemodal",
            title=self.title,
            width=400,
            handler=PeakCenterConfigHandler(),
        )
        return v


class PeakCenterConfigurer(ItemConfigurer):
    item_klass = PeakCenterConfig
    title = "Peak Center Configuration"

    detectors = List
    isotopes = List
    integration_times = List
    available_detectors = List
    display_detector_choice = True

    def _root_default(self):
        return paths.peak_center_config_dir

    def load(self, **kw):
        kw["detectors"] = self.detectors
        kw["isotopes"] = self.isotopes
        kw["available_detectors"] = self.detectors
        kw["integration_times"] = self.integration_times
        super(PeakCenterConfigurer, self).load(**kw)

        det = self.active_item.detector
        self.active_item.detector = ""
        self.active_item.detector = det

    def get(self, *args, **kw):
        item = super(PeakCenterConfigurer, self).get(*args, **kw)
        item.trait_set(
            detectors=self.detectors,
            isotopes=self.isotopes,
            available_detectors=self.detectors,
            integration_times=self.integration_times,
        )

        det = item.detector
        item.detector = ""
        item.detector = det
        return item


# if __name__ == '__main__':
#     from pychron.paths import paths
#
#     paths.build('_dev')
#
#     p = PeakCenterConfigurer()
#     p.load()
#     p.configure_traits()

# ============= EOF =============================================
