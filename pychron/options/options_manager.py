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

import apptools.sweet_pickle as pickle
from traits.api import Str, List, Button, Instance, Tuple
from traitsui.api import Controller


# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.globals import globalv
from pychron.loggable import Loggable
from pychron.options.blanks import BlanksOptions
from pychron.options.flux import FluxOptions
from pychron.options.icfactor import ICFactorOptions
from pychron.options.ideogram import IdeogramOptions
from pychron.options.iso_evo import IsotopeEvolutionOptions
from pychron.options.isochron import InverseIsochronOptions
from pychron.options.options import BaseOptions, SubOptions
from pychron.options.series import SeriesOptions
from pychron.options.spectrum import SpectrumOptions
from pychron.options.views import view
from pychron.paths import paths


class OptionsManager(Loggable):
    selected = Str
    names = List
    subview_names = Tuple
    subview = Instance(SubOptions)
    selected_subview = Str
    selected_options = Instance(BaseOptions)
    options_klass = None

    id = ''
    _defaults_path = Str

    _cached_names = List
    _cached_detectors = List

    def __init__(self, *args, **kw):
        super(OptionsManager, self).__init__(*args, **kw)
        self._populate()
        self._initialize()

    def set_detectors(self, dets):
        self._cached_detectors = dets
        if self.selected_options:
            self.selected_options.set_detectors(dets)

    def set_names(self, names):
        self._cached_names = names
        if self.selected_options:
            self.selected_options.set_names(names)

            # for p in self.plotter_options_list:
            #     p.set_names(names)

    def _selected_options_changed(self, new):
        if new:
            if self._cached_names:
                new.set_names(self._cached_names)
            if self._cached_detectors:
                new.set_detectors(self._cached_detectors)

    def set_selected(self, obj):
        for name in self.names:
            if obj.name == name:
                self.selected_options = obj

    def save(self):
        # dump the default plotter options
        if not os.path.isdir(self.persistence_root):
            try:
                os.mkdir(self.persistence_root)
            except OSError:
                os.mkdir(os.path.dirname(self.persistence_root))
                os.mkdir(self.persistence_root)

        with open(self.selected_options_path, 'w') as wfile:
            pickle.dump(self.selected, wfile)

        with open(os.path.join(self.persistence_root, '{}.p'.format(self.selected)), 'w') as wfile:
            pickle.dump(self.selected_options, wfile)
            #
            # self.plotter_options.dump(self.persistence_root)
            # self._plotter_options_list_dirty = True
            #
            # self.plotter_options = next((pp for pp in self.plotter_options_list if pp.name == name), None)
            # self._dump()

    def factory_default(self):
        if os.path.isfile(self._defaults_path):
            self.selected_options.load_factory_defaults(self._defaults_path)

    def _initialize(self):
        selected = self._load_selected_po()
        self.selected = selected

    def _load_selected_po(self):
        p = self.selected_options_path
        n = 'Default'
        if os.path.isfile(p):
            with open(p, 'r') as rfile:
                try:
                    n = pickle.load(rfile)
                except (pickle.PickleError, EOFError):
                    n = 'Default'
        return n

    def _populate(self):
        self.names = ['Default', 'Foo', 'Bar']

    def _selected_subview_changed(self, new):
        print 'subview changed {}'.format(new)
        v = self.selected_options.get_subview(new)
        print v
        self.subview = v

    def _selected_changed(self, new):
        print 'selected change {}'.format(new)
        if new:
            obj = None
            p = os.path.join(self.persistence_root, '{}.p'.format(new.lower()))
            if os.path.isfile(p):
                try:
                    with open(p, 'r') as rfile:
                        obj = pickle.load(rfile)
                except BaseException:
                    pass

            if obj is None:
                obj = self.options_klass()

            obj.initialize()
            obj.name = new
            self.subview_names = obj.subview_names
            self.selected_options = obj
            self.selected_subview = 'Main'
            # self.selected_options = self.options_klass.open(self.persistence_root, self.id, new)
        else:
            self.selected_options = None

    # def _add_options_fired(self):
    #     info = self.edit_traits(view='new_options_name_view')
    #     if info.result:
    #         self.plotter_options.name = self.new_options_name
    #         self.plotter_options.dump(self.persistence_root)
    #
    #         self._plotter_options_list_dirty = True
    #         self.set_plotter_options(self.new_options_name)

    # def _delete_options_fired(self):
    #     po = self.plotter_options
    #     if self.confirmation_dialog('Are you sure you want to delete {}'.format(po.name)):
    #         p = os.path.join(self.persistence_root, po.name)
    #         os.remove(p)
    #         self._plotter_options_list_dirty = True
    #         self.plotter_options = self.plotter_options_list[0]
    @property
    def selected_options_path(self):
        return os.path.join(self.persistence_root, 'selected.p')

    @property
    def persistence_root(self):
        return os.path.join(paths.plotter_options_dir,
                            globalv.username,
                            self.id)


class FigureOptionsManager(OptionsManager):
    pass


class IdeogramOptionsManager(FigureOptionsManager):
    id = 'ideogram'
    options_klass = IdeogramOptions
    _defaults_path = paths.ideogram_defaults


class SpectrumOptionsManager(FigureOptionsManager):
    id = 'spectrum'
    options_klass = SpectrumOptions
    _defaults_path = paths.spectrum_defaults


class SeriesOptionsManager(FigureOptionsManager):
    id = 'series'
    options_klass = SeriesOptions


class IsotopeEvolutionOptionsManager(FigureOptionsManager):
    id = 'iso_evo'
    options_klass = IsotopeEvolutionOptions


class BlanksOptionsManager(FigureOptionsManager):
    id = 'blanks'
    options_klass = BlanksOptions


class ICFactorOptionsManager(FigureOptionsManager):
    id = 'icfactor'
    options_klass = ICFactorOptions


class FluxOptionsManager(FigureOptionsManager):
    id = 'flux'
    options_klass = FluxOptions


class InverseIsochronOptionsManager(FigureOptionsManager):
    id = 'inverse_isochron'
    options_klass = InverseIsochronOptions


class OptionsController(Controller):
    delete_options = Button
    add_options = Button
    save_options = Button
    factory_default = Button

    def controller_delete_options_changed(self, info):
        print 'delete'

    def controller_add_options_changed(self, info):
        print 'add'

    def controller_save_options_changed(self, info):
        self.model.save()

    def controller_factory_default_changed(self, info):
        print 'factory'
        self.model.factory_default()


if __name__ == '__main__':
    paths.build('_dev')
    # om = IdeogramOptionsManager()
    om = OptionsController(model=SeriesOptionsManager())
    om.configure_traits(view=view('Seires'))

# ============= EOF =============================================
