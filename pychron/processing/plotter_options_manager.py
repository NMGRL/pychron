# ===============================================================================
# Copyright 2012 Jake Ross
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
from traits.api import Property, List, Event, Instance, Button, cached_property, Str, \
    HasTraits, Enum, Bool
from traits.trait_errors import TraitError
from traitsui.api import View, Item, EnumEditor, HGroup, UItem, VGroup
import apptools.sweet_pickle as pickle
# ============= standard library imports ========================
import os
# ============= local library imports  ==========================
from pychron.envisage.icon_button_editor import icon_button_editor
from pychron.globals import globalv
from pychron.processing.plotters.formatting_options import FormattingOptions
from pychron.processing.plotters.options.base import BasePlotterOptions
from pychron.processing.plotters.options.composite import CompositeOptions
from pychron.processing.plotters.options.dashboard import DashboardOptions
from pychron.processing.plotters.options.ideogram import IdeogramOptions
from pychron.processing.plotters.options.isochron import InverseIsochronOptions
from pychron.processing.plotters.options.plotter import PlotterOptions
from pychron.processing.plotters.options.series import SeriesOptions
from pychron.processing.plotters.options.spectrum import SpectrumOptions
from pychron.processing.plotters.options.system_monitor import SystemMonitorOptions
from pychron.paths import paths
from pychron.processing.plotters.options.xy_scatter import XYScatterOptions
from pychron.pychron_constants import NULL_STR


class PlotterOptionsManager(HasTraits):
    plotter_options_list = Property(List(BasePlotterOptions), depends_on='_plotter_options_list_dirty')
    _plotter_options_list_dirty = Event
    plotter_options = Instance(BasePlotterOptions)
    plotter_options_name = 'main'
    plotter_options_klass = PlotterOptions

    delete_options = Button
    add_options = Button
    save_options = Button
    factory_default = Button

    new_options_name = Str
    persistence_name = ''
    persistence_root = Property
    _defaults_path = Str

    formatting_option = Enum('Screen', 'Presentation', 'Display', NULL_STR)
    use_formatting_options = Bool

    def __init__(self, *args, **kw):
        super(PlotterOptionsManager, self).__init__(*args, **kw)
        self._load()

    def _load(self):
        p = paths.plotter_options
        if os.path.isfile(p):
            with open(p, 'r') as rfile:
                try:
                    pd = pickle.load(rfile)
                    self.trait_set(**pd)
                except (pickle.PickleError, TraitError):
                    pass

    def _dump(self):
        with open(paths.plotter_options, 'w') as wfile:
            d = {'formatting_option': self.formatting_option or NULL_STR,
                 'use_formatting_options': self.use_formatting_options}
            try:
                pickle.dump(d, wfile)
            except pickle.PickleError:
                pass

    def deinitialize(self):
        if self.plotter_options:
            self.plotter_options.deinitialize()

    def load_yaml(self, blob):
        po = self.plotter_options_klass(self.persistence_root)
        po.load_yaml(blob)
        self.plotter_options = po
        po.initialize()

    def dump_yaml(self):
        po = self.plotter_options
        return po.dump_yaml()

    def _get_persistence_root(self):
        return os.path.join(paths.plotter_options_dir,
                            globalv.username,
                            self.persistence_name)

    def close(self):
        self.save()

    def save(self):
        # dump the default plotter options
        if not os.path.isdir(self.persistence_root):
            try:
                os.mkdir(self.persistence_root)
            except OSError:
                os.mkdir(os.path.dirname(self.persistence_root))
                os.mkdir(self.persistence_root)

        p = os.path.join(self.persistence_root,
                         '{}.default'.format(self.plotter_options_name))
        name = self.plotter_options.name
        with open(p, 'w') as wfile:
            pickle.dump(name, wfile)

        self.plotter_options.dump(self.persistence_root)
        self._plotter_options_list_dirty = True

        self.plotter_options = next((pp for pp in self.plotter_options_list if pp.name == name), None)
        self._dump()

    def set_plotter_options(self, name):
        self.plotter_options = next((pi for pi in self.plotter_options_list
                                     if pi.name == name), None)

    def _factory_default(self):
        """
            read defaults from yaml file
        """
        if os.path.isfile(self._defaults_path):
            self.plotter_options.load_factory_defaults(self._defaults_path)

    # ===============================================================================
    # handlers
    # ===============================================================================
    def _formatting_option_factory(self):
        p = getattr(paths, '{}_formatting_options'.format(self.formatting_option.lower()))
        fmt = FormattingOptions(p)
        return fmt

    def _use_formatting_options_changed(self, new):
        print new
        if not new:
            if self.plotter_options:
                self.plotter_options.formatting_options = None
                self.plotter_options.refresh_plot_needed = True
        else:
            self._formatting_option_changed(self.formatting_option)

    def _formatting_option_changed(self, new):
        if self.plotter_options:
            fmt = None if new == NULL_STR else self._formatting_option_factory()
            print new, fmt
            if self.use_formatting_options:
                self.plotter_options.formatting_options = fmt
                self.plotter_options.refresh_plot_needed = True

    def _plotter_options_changed(self, new):
        if new:
            if self.use_formatting_options:
                fmt = self._formatting_option_factory()
                new.formatting_options = fmt

    def _factory_default_fired(self):
        self._factory_default()
        self.plotter_options.refresh_plot_needed = True

    def _save_options_fired(self):
        self.save()

    def _add_options_fired(self):
        info = self.edit_traits(view='new_options_name_view')
        if info.result:
            self.plotter_options.name = self.new_options_name
            self.plotter_options.dump(self.persistence_root)

            self._plotter_options_list_dirty = True
            self.set_plotter_options(self.new_options_name)

    def _delete_options_fired(self):
        po = self.plotter_options
        if self.confirmation_dialog('Are you sure you want to delete {}'.format(po.name)):
            p = os.path.join(self.persistence_root, po.name)
            os.remove(p)
            self._plotter_options_list_dirty = True
            self.plotter_options = self.plotter_options_list[0]

    def new_options_name_view(self):
        v = View(
            Item('new_options_name', label='New Plot Options Name'),
            width=500,
            title=' ',
            buttons=['OK', 'Cancel'],
            kind='livemodal')
        return v

    def traits_view(self):
        v = View(
            VGroup(HGroup(
                Item('plotter_options', show_label=False,
                     editor=EnumEditor(name='plotter_options_list'),
                     tooltip='List of available plot options'),
                icon_button_editor('add_options',
                                   'add',
                                   tooltip='Add new plot options', ),
                icon_button_editor('delete_options',
                                   'delete',
                                   tooltip='Delete current plot options',
                                   enabled_when='object.plotter_options.name!="Default"', ),
                icon_button_editor('save_options', 'disk',
                                   tooltip='Save changes to options'),
                icon_button_editor('factory_default', 'edit-bomb',
                                   tooltip='Apply factory defaults')),
                HGroup(UItem('use_formatting_options'),
                       UItem('formatting_option', enabled_when='use_formatting_options')),

                Item('plotter_options',
                     show_label=False,
                     style='custom')),
            resizable=True)
        return v

    @cached_property
    def _get_plotter_options_list(self):
        klass = self.plotter_options_klass
        ps = [klass(self.persistence_root, name='Default')]
        if os.path.isdir(self.persistence_root):
            for n in os.listdir(self.persistence_root):
                if n.startswith('.') or n.endswith('.default') or n == 'Default':
                    continue

                po = klass(self.persistence_root, name=n)
                ps.append(po)
        return ps

    def _plotter_options_default(self):

        n = self._load_selected_po()
        po = next((pi for pi in self.plotter_options_list if pi.name == n), None)
        if not po:
            po = self.plotter_options_list[0]
        self._plotter_options_changed(po)
        return po

    def _load_selected_po(self):
        p = os.path.join(self.persistence_root, '{}.default'.format(self.plotter_options_name))

        n = 'Default'
        if os.path.isfile(p):
            with open(p, 'r') as rfile:
                try:
                    n = pickle.load(rfile)
                except (pickle.PickleError, EOFError):
                    n = 'Default'
        return n


class IdeogramOptionsManager(PlotterOptionsManager):
    plotter_options_klass = IdeogramOptions
    persistence_name = 'ideogram'
    _defaults_path = paths.ideogram_defaults


class SpectrumOptionsManager(PlotterOptionsManager):
    plotter_options_klass = SpectrumOptions
    persistence_name = 'spectrum'
    _defaults_path = paths.spectrum_defaults


class InverseIsochronOptionsManager(PlotterOptionsManager):
    plotter_options_klass = InverseIsochronOptions
    persistence_name = 'inverse_isochron'
    _defaults_path = paths.inverse_isochron_defaults


class SeriesOptionsManager(PlotterOptionsManager):
    plotter_options_klass = SeriesOptions
    persistence_name = 'series'


class SystemMonitorOptionsManager(PlotterOptionsManager):
    plotter_options_klass = SystemMonitorOptions
    persistence_name = 'system_monitor'


class SysMonIdeogramOptionsManager(IdeogramOptionsManager):
    persistence_name = 'sys_mon_ideogram'
    _defaults_path = paths.sys_mon_ideogram_defaults


class DashboardOptionsManager(PlotterOptionsManager):
    plotter_options_klass = DashboardOptions
    persistence_name = 'dashboard'


class XYScatterOptionsManager(PlotterOptionsManager):
    plotter_options_klass = XYScatterOptions
    persistence_name = 'xy_scatter'


class CompositeOptionsManager(PlotterOptionsManager):
    plotter_options_klass = CompositeOptions
    persistence_name = 'composite'
    _defaults_path = paths.composites_defaults

# ============= EOF =============================================
