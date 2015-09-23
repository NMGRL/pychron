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
import apptools.sweet_pickle as pickle
from traits.api import Str, List, Button, Instance, Tuple, Property
from traitsui.api import Controller, View, Item
# ============= standard library imports ========================
import os
# ============= local library imports  ==========================
from pychron.core.helpers.filetools import list_directory2
from pychron.file_defaults import SPECTRUM_SCREEN, IDEOGRAM_SCREEN, IDEOGRAM_PRESENTATION, SERIES_SCREEN, BLANKS_SCREEN, \
    ICFACTOR_SCREEN, INVERSE_ISOCHRON_SCREEN, INVERSE_ISOCHRON_PRESENTATION, ISO_EVO_SCREEN, BLANKS_PRESENTATION
from pychron.file_defaults import SPECTRUM_PRESENTATION
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
    new_name = Property
    _new_name = Str
    id = ''
    # _defaults_path = Str
    _defaults = None

    _cached_names = List
    _cached_detectors = List
    _default_options_txt = None

    def __init__(self, *args, **kw):
        super(OptionsManager, self).__init__(*args, **kw)
        self._populate()
        self._initialize()

    def _get_new_name(self):
        return self._new_name

    def _set_new_name(self, v):
        self._new_name = v

    def _validate_new_name(self, v):
        if v not in self.names:
            return v

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

    def save_selection(self):
        if not os.path.isdir(self.persistence_root):
            try:
                os.mkdir(self.persistence_root)
            except OSError:
                os.mkdir(os.path.dirname(self.persistence_root))
                os.mkdir(self.persistence_root)

        if self.selected:
            with open(self.selected_options_path, 'w') as wfile:
                pickle.dump(self.selected, wfile)

    def save(self, name=None, obj=None):
        # dump the default plotter options
        self.save_selection()

        if self.selected:
            obj = self.selected_options
            name = self.selected

        with open(os.path.join(self.persistence_root, '{}.p'.format(name)), 'w') as wfile:
            pickle.dump(obj, wfile)

    def add(self, name):
        p = self.options_klass()
        p.load_factory_defaults(self._default_options_txt)
        self.save(name, p)
        self._load_names()
        self.selected = name

    def factory_default(self):
        self.debug('set factory default')
        if self._defaults:
            options_name = self.selected.lower()
            for name, txt in self._defaults:
                if name == options_name:
                    self.debug('set factory default for {}'.format(name))
                    dp = os.path.join(self.persistence_root, '{}.p'.format(name))
                    os.remove(dp)

                    p = self.options_klass()
                    p.load_factory_defaults(txt)
                    self.save(name, p)
                    break

                    # warning(None, 'Factory defaults temporarily disabled')

                    # print  os.path.isfile(self._defaults_path), self._defaults_path
                    # if os.path.isfile(self._defaults_path):
                    #     self.debug('load factory defaults {}'.format(self._defaults_path))
                    #     self.selected_options.load_factory_defaults(self._defaults_path)

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
        # write some defaults
        if self._defaults:
            for name, txt in self._defaults:
                dp = os.path.join(self.persistence_root, '{}.p'.format(name))
                if not os.path.isfile(dp):
                    p = self.options_klass()
                    p.load_factory_defaults(txt)
                    self.save(name, p)

        self._load_names()

    def _load_names(self):
        self.names = [n for n in list_directory2(self.persistence_root,
                                                 extension='.p',
                                                 remove_extension=True) if n != 'selected']

    def _selected_subview_changed(self, new):
        if new:
            v = self.selected_options.get_subview(new)
            self.subview = v

    def _selected_changed(self, new):
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

            o = self.selected_subview
            if not o:
                o = 'Main'

            self.selected_subview = ''
            self.selected_subview = o

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


class IsotopeEvolutionOptionsManager(FigureOptionsManager):
    id = 'iso_evo'
    options_klass = IsotopeEvolutionOptions
    _default_options_txt = ISO_EVO_SCREEN


class FluxOptionsManager(FigureOptionsManager):
    id = 'flux'
    options_klass = FluxOptions


class IdeogramOptionsManager(FigureOptionsManager):
    id = 'ideogram'
    options_klass = IdeogramOptions
    _defaults = (('screen', IDEOGRAM_SCREEN),
                 ('presentation', IDEOGRAM_PRESENTATION))
    _default_options_txt = IDEOGRAM_SCREEN


class SpectrumOptionsManager(FigureOptionsManager):
    id = 'spectrum'
    options_klass = SpectrumOptions
    _defaults = (('screen', SPECTRUM_SCREEN),
                 ('presentation', SPECTRUM_PRESENTATION))
    _default_options_txt = SPECTRUM_SCREEN


class SeriesOptionsManager(FigureOptionsManager):
    id = 'series'
    options_klass = SeriesOptions
    _defaults = (('screen', SERIES_SCREEN),)
    _default_options_txt = SERIES_SCREEN


class BlanksOptionsManager(FigureOptionsManager):
    id = 'blanks'
    options_klass = BlanksOptions
    _defaults = (('screen', BLANKS_SCREEN),
                 ('presentation', BLANKS_PRESENTATION))
    _default_options_txt = BLANKS_SCREEN


class ICFactorOptionsManager(FigureOptionsManager):
    id = 'icfactor'
    options_klass = ICFactorOptions
    _defaults = (('screen', ICFACTOR_SCREEN),)
    _default_options_txt = ICFACTOR_SCREEN


class InverseIsochronOptionsManager(FigureOptionsManager):
    id = 'inverse_isochron'
    options_klass = InverseIsochronOptions
    _defaults = (('screen', INVERSE_ISOCHRON_SCREEN),
                 ('presentation', INVERSE_ISOCHRON_PRESENTATION))
    _default_options_txt = INVERSE_ISOCHRON_SCREEN


class OptionsController(Controller):
    delete_options = Button
    add_options = Button
    save_options = Button
    factory_default = Button

    def closed(self, info, is_ok):
        if is_ok:
            self.model.save_selection()

    def controller_delete_options_changed(self, info):
        print 'delete'

    def controller_add_options_changed(self, info):
        info = self.edit_traits(view=View(Item('new_name', label='Name'),
                                          title='New Options',
                                          kind='livemodal',
                                          buttons=['OK', 'Cancel']))
        if info.result:
            self.model.add(self.model.new_name)

    def controller_save_options_changed(self, info):
        self.model.save()

    def controller_factory_default_changed(self, info):
        self.model.factory_default()


if __name__ == '__main__':
    paths.build('_dev')
    # om = IdeogramOptionsManager()
    om = OptionsController(model=SeriesOptionsManager())
    om.configure_traits(view=view('Series'))

# ============= EOF =============================================
