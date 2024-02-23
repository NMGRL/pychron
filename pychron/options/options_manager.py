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
import json
import os
import pickle
import shutil
import sys

from traits.api import Str, List, Button, Instance, Tuple, Property, cached_property
from traitsui.api import Controller, Item

from pychron.core.helpers.filetools import glob_list_directory, add_extension
from pychron.core.helpers.isotope_utils import sort_detectors
from pychron.core.helpers.strtools import ratio
from pychron.core.helpers.traitsui_shortcuts import okcancel_view
from pychron.file_defaults import (
    SPECTRUM_PRESENTATION,
    RADIAL_SCREEN,
    REGRESSION_SERIES_SCREEN,
    DEFINE_EQUILIBRATION_SCREEN,
)
from pychron.file_defaults import (
    SPECTRUM_SCREEN,
    IDEOGRAM_SCREEN,
    IDEOGRAM_PRESENTATION,
    SERIES_SCREEN,
    BLANKS_SCREEN,
    ICFACTOR_SCREEN,
    INVERSE_ISOCHRON_SCREEN,
    INVERSE_ISOCHRON_PRESENTATION,
    ISO_EVO_SCREEN,
    BLANKS_PRESENTATION,
)
from pychron.globals import globalv
from pychron.loggable import Loggable
from pychron.mdd.tasks.mdd_figure import MDDFigureOptions
from pychron.options.arar_calculations import ArArCalculationsOptions
from pychron.options.blanks import BlanksOptions
from pychron.options.composite import CompositeOptions
from pychron.options.define_equilibration import DefineEquilibrationOptions
from pychron.options.flux import (
    FluxOptions,
    VerticalFluxOptions,
    FluxVisualizationOptions,
)
from pychron.options.icfactor import ICFactorOptions
from pychron.options.ideogram import IdeogramOptions
from pychron.options.iso_evo import IsotopeEvolutionOptions
from pychron.options.isochron import InverseIsochronOptions
from pychron.options.options import BaseOptions, SubOptions, importklass
from pychron.options.radial import RadialOptions
from pychron.options.ratio_series import RatioSeriesOptions
from pychron.options.regression import RegressionOptions
from pychron.options.regression_series import RegressionSeriesOptions
from pychron.options.series import SeriesOptions
from pychron.options.spectrum import SpectrumOptions
from pychron.options.xy_scatter import XYScatterOptions
from pychron.paths import paths
from pychron.pipeline.plot.plotter.series import (
    PEAK_CENTER,
    ANALYSIS_TYPE,
    LAB_TEMP,
    LAB_HUM,
    EXTRACT_DURATION,
    RADIOGENIC_YIELD,
    AGE,
    F,
)
from pychron.pychron_constants import (
    EXTRACT_VALUE,
    CLEANUP,
    UNKNOWN,
    COCKTAIL,
    DETECTOR_IC,
)


class OptionsUnpickler(pickle.Unpickler):
    def __init__(self, *args, **kw):
        super(OptionsUnpickler, self).__init__(*args, **kw)
        try:
            self.dispatch["oreduce"] = self.dispatch[pickle.REDUCE[0]]
            self.dispatch["obuild"] = self.dispatch[pickle.BUILD[0]]
            self.dispatch[pickle.REDUCE[0]] = self.load_reduce
            self.dispatch[pickle.BUILD[0]] = self.load_build
        except AttributeError:
            pass

    def destroy(self):
        try:
            self.dispatch[pickle.REDUCE[0]] = self.dispatch["oreduce"]
            self.dispatch[pickle.BUILD[0]] = self.dispatch["obuild"]
        except AttributeError:
            pass

    def find_class(self, mod, klass):
        if klass == "QColor":
            from pyface.qt.QtGui import QColor

            r = QColor
        else:
            r = super(OptionsUnpickler, self).find_class(mod, klass)

        return r

    @classmethod
    def load_reduce(cls, obj):
        stack = obj.stack
        args = stack.pop()
        func = stack[-1]
        if args and args[0] == "PyQt4.QtGui":
            try:
                stack[-1] = func(*args)
            except ModuleNotFoundError:
                from pyface.qt.QtGui import QColor

                stack[-1] = QColor(*args[2])
        else:
            stack[-1] = func(*args)

    @classmethod
    def load_build(cls, obj):
        stack = obj.stack
        state = stack.pop()
        inst = stack[-1]
        setstate = getattr(inst, "__setstate__", None)
        if setstate is not None:
            setstate(state)
            return
        slotstate = None
        if isinstance(state, tuple) and len(state) == 2:
            state, slotstate = state

        if state == "setRgbF":
            inst.setRgbF(*slotstate)
        else:
            if state:
                inst_dict = inst.__dict__
                intern = sys.intern

                for k, v in state.items():
                    if type(k) is str:
                        inst_dict[intern(k)] = v
                    else:
                        inst_dict[k] = v
            if slotstate:
                for k, v in slotstate.items():
                    setattr(inst, k, v)


class BaseOptionsManager(Loggable):
    names = List
    selected = Str
    _defaults = None
    new_name = Property
    _new_name = Str
    delete_enabled = Property(depends_on="names")

    id = ""

    def __init__(self, *args, **kw):
        super(BaseOptionsManager, self).__init__(*args, **kw)
        self._populate()
        self._initialize()

    def delete_selected(self):
        if self.confirmation_dialog(
            'Are you sure you want to delete "{}"'.format(self.selected)
        ):
            for ext in (".p", ".json"):
                p = self._pname(self.selected, ext)
                if os.path.isfile(p):
                    os.remove(p)
                    break
            self.refresh()

    def refresh(self):
        self._load_names()
        self._initialize()

    def save_selected(self):
        if not os.path.isdir(self.persistence_root):
            try:
                os.mkdir(self.persistence_root)
            except OSError:
                os.mkdir(os.path.dirname(self.persistence_root))
                os.mkdir(self.persistence_root)

        if self.selected:
            with open(self._pname("selected", ".json"), "w") as wfile:
                json.dump({"selected": self.selected}, wfile)

            p = self._pname("selected")
            if os.path.isfile(p):
                os.remove(p)

    def save_selected_as(self):
        name = self.new_name

        self._save(name, self.selected_options)

        self.refresh()
        self.selected = name
        self.save_selected()

    def save(self, name=None, obj=None):
        # dump the default plotter options
        self.save_selected()

        if name is None:
            if self.selected:
                obj = self.selected_options
                name = self.selected

        self._save(name, obj)
        self._load_names()

    def _selected_changed(self, new):
        self._option_factory(new)

    def _option_factory(self, new):
        if new:
            obj = None
            name = new.lower()

            yp = self._pname(name, ".json")
            if os.path.isfile(yp):
                obj = options_load_json(yp)
                if obj:
                    obj.manager_id = self.id
                    p = self._pname(name)
                    if os.path.isfile(p):
                        dp = self._pname(name, ".p.bak")
                        shutil.move(p, dp)

            if obj is None:
                p = self._pname(name)
                if os.path.isfile(p):
                    unp = None
                    try:
                        with open(p, "rb") as rfile:
                            unp = OptionsUnpickler(rfile)
                            obj = unp.load()
                    except BaseException as e:
                        self.debug_exception()
                    finally:
                        if unp:
                            unp.destroy()

            if obj is None:
                obj = self.options_klass()

            obj.initialize()
            obj.setup()

            obj.name = new
            self.selected_options = obj
        else:
            self.selected_options = None

        return obj

    def _pname(self, name, ext=".p"):
        name = add_extension(name, ext)
        return os.path.join(self.persistence_root, name)

    def _initialize(self):
        p = self._pname("selected", ".json")
        n = "Default"
        if os.path.isfile(p):
            with open(p, "r") as rfile:
                obj = json.load(rfile)
                n = obj["selected"]
        else:
            p = self._pname("selected")
            if os.path.isfile(p):
                with open(p, "rb") as rfile:
                    try:
                        n = pickle.load(rfile)
                    except (pickle.PickleError, EOFError):
                        n = "Default"

        self.selected = n

    def _populate(self):
        # write some defaults
        if self._defaults:
            for name, txt in self._defaults:
                dp = self._pname(name)
                if not os.path.isfile(dp):
                    p = self.options_klass()
                    p.load_factory_defaults(txt)
                    self.save(name, p)

        self._load_names()

    def _load_names(self):
        ps = glob_list_directory(
            self.persistence_root, extension=".p", remove_extension=True
        )
        js = glob_list_directory(
            self.persistence_root, extension=".json", remove_extension=True
        )

        ps.extend(js)
        self.names = [ni for ni in ps if ni != "selected"]

    @cached_property
    def _get_delete_enabled(self):
        return len(self.names) > 1

    def _get_new_name(self):
        return self._new_name

    def _set_new_name(self, v):
        self._new_name = v

    def _validate_new_name(self, v):
        if all((a not in v) for a in ("\\", " ", "/")):
            if v not in self.names:
                return v

    @classmethod
    def persistence_root(cls):
        return os.path.join(paths.appdata_dir, globalv.username, cls.id)


def options_load_json(p):
    with open(p, "r") as rfile:
        try:
            j = json.load(rfile)
        except json.JSONDecodeError:
            return

    klass = j.get("klass")
    if klass is None:
        return

    cls = importklass(klass)
    obj = cls()
    obj.load(j)
    return obj


class OptionsManager(BaseOptionsManager):
    subview_names = Tuple
    subview = Instance(SubOptions)
    selected_subview = Str
    selected_options = Instance(BaseOptions)
    options_klass = None

    _cached_names = List
    _cached_detectors = List
    _cached_atypes = List
    _cached_reference_types = List
    _cached_options = None

    _default_options_txt = None

    def set_detectors(self, dets):
        self._cached_detectors = dets
        if self.selected_options:
            self.selected_options.set_detectors(dets)

    def set_names(self, names, *args, **kw):
        self._cached_names = names
        if self.selected_options:
            self.selected_options.set_names(names, *args, **kw)

            # for p in self.plotter_options_list:
            #     p.set_names(names)

    def set_outside_options(self, options):
        self._cached_options = options
        if self.selected_options:
            options.clone_to(self.selected_options)

    def set_analysis_types(self, atypes):
        self._cached_atypes = atypes
        if self.selected_options:
            self.selected_options.set_analysis_types(atypes)

    def set_reference_types(self, atypes):
        self._cached_reference_types = atypes
        if self.selected_options:
            self.selected_options.set_reference_types(atypes)

    def _selected_options_changed(self, new):
        if new:
            if self._cached_names:
                new.set_names(self._cached_names)

            if self._cached_detectors:
                new.set_detectors(self._cached_detectors)

            if self._cached_atypes:
                new.set_analysis_types(self._cached_atypes)

            if self._cached_reference_types:
                new.set_reference_types(self._cached_reference_types)

            if self._cached_options:
                self._cached_options.clone_to(new)

    def set_selected(self, obj):
        for name in self.names:
            if obj.name == name:
                self.selected_options = obj

    def add(self, name):
        p = self.options_klass()
        p.load_factory_defaults(self._default_options_txt)
        self.save(name, p)
        self._load_names()

        self.selected = name

    def factory_default(self):
        self.debug("set factory default")
        if self._defaults:
            options_name = self.selected.lower()
            for name, txt in self._defaults:
                if name == options_name:
                    self.selected = ""
                    self.debug("set factory default for {}".format(name))
                    dp = self._pname(name)
                    os.remove(dp)

                    p = self.options_klass()
                    p.load_factory_defaults(txt)
                    self.save(name, p)

                    self.selected = name
                    break
            else:
                self.information_dialog(
                    'Factory Defaults not available for "{}". '
                    "Not a factory provided options set".format(options_name)
                )

        else:
            self.information_dialog("Not Factory Defaults available")

    def _selected_subview_changed(self, new):
        if new:
            v = self.selected_options.get_subview(new)
            self.subview = v

    def _save(self, name, obj):
        p = self._pname(name, ".json")
        with open(p, "w") as wfile:
            obj.dump(wfile)

        # for backwards compatiblity keep this for now
        p = self._pname(name)
        if os.path.isfile(p):
            dp = self._pname(name, ".p.bak")
            shutil.move(p, dp)

        # p = self._pname(name)
        # with open(p, 'wb') as wfile:
        #     spickle.dump(obj, wfile)

    def _selected_changed(self, new):
        obj = self._option_factory(new)
        if obj:
            self.subview_names = obj.subview_names

            o = self.selected_subview
            if not o and self.subview_names:
                o = self.subview_names[0]

            self.selected_subview = ""
            self.selected_subview = o

        # else:
        #     self.selected_options = None

    @property
    def persistence_root(self):
        return os.path.join(paths.plotter_options_dir, globalv.username, self.id)


class ArArCalculationsOptionsManager(OptionsManager):
    id = "arar_calculations"
    options_klass = ArArCalculationsOptions


class FigureOptionsManager(OptionsManager):
    pass


class IsotopeEvolutionOptionsManager(FigureOptionsManager):
    id = "iso_evo"
    options_klass = IsotopeEvolutionOptions
    _default_options_txt = ISO_EVO_SCREEN


class DefineEquilibrationOptionsManager(FigureOptionsManager):
    id = "define_equilibration"
    options_klass = DefineEquilibrationOptions
    _default_options_txt = DEFINE_EQUILIBRATION_SCREEN


class FluxOptionsManager(FigureOptionsManager):
    id = "flux"
    options_klass = FluxOptions


class VerticalFluxOptionsManager(FigureOptionsManager):
    id = "vertical_flux"
    options_klass = VerticalFluxOptions


class FluxVisualizationOptionsManager(FigureOptionsManager):
    id = "flux_visualization"
    options_klass = FluxVisualizationOptions


class XYScatterOptionsManager(FigureOptionsManager):
    id = "xy_scatter"
    options_klass = XYScatterOptions


class IdeogramOptionsManager(FigureOptionsManager):
    id = "ideogram"
    options_klass = IdeogramOptions
    _defaults = (("screen", IDEOGRAM_SCREEN), ("presentation", IDEOGRAM_PRESENTATION))
    _default_options_txt = IDEOGRAM_SCREEN


class SpectrumOptionsManager(FigureOptionsManager):
    id = "spectrum"
    options_klass = SpectrumOptions
    _defaults = (("screen", SPECTRUM_SCREEN), ("presentation", SPECTRUM_PRESENTATION))
    _default_options_txt = SPECTRUM_SCREEN


class SeriesOptionsManager(FigureOptionsManager):
    id = "series"
    options_klass = SeriesOptions
    _defaults = (("screen", SERIES_SCREEN),)
    _default_options_txt = SERIES_SCREEN

    def set_names_via_keys(
        self, iso_keys, analysis_type=None, detectors=None, additional_names=None
    ):
        names = []
        if iso_keys:
            names.extend(iso_keys)
            names.extend(["{}bs".format(ki) for ki in iso_keys])
            names.extend(["{}ic".format(ki) for ki in iso_keys])

            names.extend(ratio(iso_keys))
            names.extend(ratio(iso_keys, invert=True))

            if analysis_type in (UNKNOWN, COCKTAIL):
                names.append(AGE)
                names.append(RADIOGENIC_YIELD)
                names.append(F)

            if analysis_type in (DETECTOR_IC,):
                for i, di in enumerate(detectors):
                    for j, dj in enumerate(detectors):
                        if j < i:
                            continue

                        if di == dj:
                            continue

                        names.append("{}/{} DetIC".format(di, dj))

        names.extend(
            [
                PEAK_CENTER,
                ANALYSIS_TYPE,
                LAB_TEMP,
                LAB_HUM,
                EXTRACT_VALUE,
                EXTRACT_DURATION,
                CLEANUP,
            ]
        )
        if additional_names:
            names.extend(additional_names)

        self.set_names(names)


class RatioSeriesOptionsManager(FigureOptionsManager):
    id = "ratio_series"
    options_klass = RatioSeriesOptions


class RegressionOptionsManager(FigureOptionsManager):
    id = "regression"
    options_klass = RegressionOptions


class BlanksOptionsManager(FigureOptionsManager):
    id = "blanks"
    options_klass = BlanksOptions
    _defaults = (("screen", BLANKS_SCREEN), ("presentation", BLANKS_PRESENTATION))
    _default_options_txt = BLANKS_SCREEN


class ICFactorOptionsManager(FigureOptionsManager):
    id = "icfactor"
    options_klass = ICFactorOptions
    _defaults = (("screen", ICFACTOR_SCREEN),)
    _default_options_txt = ICFACTOR_SCREEN


class InverseIsochronOptionsManager(FigureOptionsManager):
    id = "inverse_isochron"
    options_klass = InverseIsochronOptions
    _defaults = (
        ("screen", INVERSE_ISOCHRON_SCREEN),
        ("presentation", INVERSE_ISOCHRON_PRESENTATION),
    )
    _default_options_txt = INVERSE_ISOCHRON_SCREEN


class RegressionSeriesOptionsManager(FigureOptionsManager):
    id = "regression_series"
    options_klass = RegressionSeriesOptions
    _defaults = (("screen", REGRESSION_SERIES_SCREEN),)
    _default_options_txt = REGRESSION_SERIES_SCREEN


class RadialOptionsManager(FigureOptionsManager):
    id = "radial"
    options_klass = RadialOptions
    _defaults = (("screen", RADIAL_SCREEN),)
    _default_options_txt = RADIAL_SCREEN


class MDDFigureOptionsManager(FigureOptionsManager):
    id = "mdd"
    options_klass = MDDFigureOptions


class CompositeOptionsManager(FigureOptionsManager):
    id = "composite"
    options_klass = CompositeOptions


class OptionsController(Controller):
    delete_options = Button
    add_options = Button
    save_options = Button
    save_as_options = Button
    factory_default = Button

    def closed(self, info, is_ok):
        if is_ok:
            self.model.save_selected()

    def controller_delete_options_changed(self, info):
        self.model.delete_selected()

    def controller_add_options_changed(self, info):
        info = self.edit_traits(
            view=okcancel_view(Item("new_name", label="Name"), title="New Options")
        )
        if info.result:
            self.model.add(self.model.new_name)

    def controller_save_options_changed(self, info):
        self.model.save()

    def controller_save_as_options_changed(self, info):
        info = self.edit_traits(
            view=okcancel_view(Item("new_name", label="Name"), title="New Options")
        )
        if info.result:
            self.model.save_selected_as()

    def controller_factory_default_changed(self, info):
        self.model.factory_default()


# if __name__ == '__main__':
#     paths.build('_dev')
#     # om = IdeogramOptionsManager()
#     om = OptionsController(model=SeriesOptionsManager())
#     om.configure_traits(view=view('Series'))

# ============= EOF =============================================
