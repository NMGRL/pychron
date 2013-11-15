#===============================================================================
# Copyright 2012 Jake Ross
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#===============================================================================

#============= enthought library imports =======================
from traits.api import Property, List, Event, Instance, Button, cached_property, Str, \
    HasTraits
from traitsui.api import View, Item, EnumEditor, HGroup
import apptools.sweet_pickle as pickle
#============= standard library imports ========================
import os
#============= local library imports  ==========================
from pychron.envisage.tasks.pane_helpers import icon_button_editor
from pychron.processing.plotters.options.base import BasePlotterOptions
from pychron.processing.plotters.options.dashboard import DashboardOptions
from pychron.processing.plotters.options.ideogram import IdeogramOptions
from pychron.processing.plotters.options.isochron import InverseIsochronOptions
from pychron.processing.plotters.options.plotter import PlotterOptions
from pychron.processing.plotters.options.series import SeriesOptions
from pychron.processing.plotters.options.spectrum import SpectrumOptions
from pychron.processing.plotters.options.system_monitor import SystemMonitorOptions
from pychron.paths import paths


class PlotterOptionsManager(HasTraits):
    plotter_options_list = Property(List(BasePlotterOptions), depends_on='_plotter_options_list_dirty')
    _plotter_options_list_dirty = Event
    plotter_options = Instance(BasePlotterOptions)
    plotter_options_name = 'main'
    plotter_options_klass = PlotterOptions

    delete_options = Button('-')
    add_options = Button('+')
    save_options = Button('+')
    new_options_name = Str
    persistence_name = ''
    persistence_root = Property

    def _get_persistence_root(self):
        return os.path.join(paths.plotter_options_dir, self.persistence_name)

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
        with open(p, 'w') as fp:
            obj = self.plotter_options.name
            pickle.dump(obj, fp)

        self.plotter_options.dump(self.persistence_root)
        self._plotter_options_list_dirty = True


    def set_plotter_options(self, name):
        self.plotter_options = next((pi for pi in self.plotter_options_list
                                     if pi.name == name), None)

    #===============================================================================
    # handlers
    #===============================================================================
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
            HGroup(
                Item('plotter_options', show_label=False,
                     editor=EnumEditor(name='plotter_options_list'),
                     tooltip='List of available plot options'),
                icon_button_editor('add_options',
                                   'add',
                                   tooltip='Add new plot options',
                ),
                icon_button_editor('delete_options',
                                   'delete',
                                   tooltip='Delete current plot options',
                                   enabled_when='object.plotter_options.name!="Default"',
                ),
                icon_button_editor('save_options', 'save',
                                   tooltip='Save changes to options',
                )),
            Item('plotter_options',
                 show_label=False,
                 style='custom'),
            resizable=True,
            #handler=self.handler_klass
        )
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
        p = os.path.join(self.persistence_root, '{}.default'.format(self.plotter_options_name))

        n = 'Default'
        if os.path.isfile(p):
            with open(p, 'r') as fp:
                try:
                    n = pickle.load(fp)
                except (pickle.PickleError, EOFError):
                    n = 'Default'

        po = next((pi for pi in self.plotter_options_list if pi.name == n), None)
        if not po:
            po = self.plotter_options_list[0]

        return po


class IdeogramOptionsManager(PlotterOptionsManager):
    plotter_options_klass = IdeogramOptions
    persistence_name = 'ideogram'
    #title = 'Ideogram Plot Options'


class SpectrumOptionsManager(PlotterOptionsManager):
    plotter_options_klass = SpectrumOptions
    persistence_name = 'spectrum'
    #title = 'Spectrum Plot Options'


class InverseIsochronOptionsManager(PlotterOptionsManager):
    plotter_options_klass = InverseIsochronOptions
    persistence_name = 'inverse_isochron'
    #title = 'Isochron Plot Options'


class SeriesOptionsManager(PlotterOptionsManager):
    plotter_options_klass = SeriesOptions
    persistence_name = 'series'
    #title = 'Series Plot Options'


class SystemMonitorOptionsManager(PlotterOptionsManager):
    plotter_options_klass = SystemMonitorOptions
    persistence_name = 'system_monitor'
    #title = 'Series Plot Options'


class DashboardOptionsManager(PlotterOptionsManager):
    plotter_options_klass = DashboardOptions
    persistence_name = 'dashboard'

#============= EOF =============================================
