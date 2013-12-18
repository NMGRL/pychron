#===============================================================================
# Copyright 2013 Jake Ross
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
from traits.api import HasTraits, List, Str, TraitError, Button, Bool, Event
from traitsui.api import View, HGroup, Item, spring

import apptools.sweet_pickle as pickle
#============= standard library imports ========================
import os
#============= local library imports  ==========================
from pychron.envisage.tasks.pane_helpers import icon_button_editor
from pychron.processing.plotters.options.option import PlotterOption
from pychron.pychron_constants import NULL_STR


class BasePlotterOptions(HasTraits):
    aux_plots = List
    name = Str
    plot_option_klass = PlotterOption
    plot_option_name = None
    refresh_plot = Button
    refresh_plot_needed=Event
    auto_refresh = Bool(False)

    def __init__(self, root, clean=False, *args, **kw):
        super(BasePlotterOptions, self).__init__(*args, **kw)
        if not clean:
            self._load(root)

    def get_aux_plots(self):
        return reversed([pi
                         for pi in self.aux_plots
                         if pi.name and pi.name != NULL_STR and pi.use])

    def traits_view(self):
        v = View()
        return v

    def _refresh_plot_fired(self):
        print 'asdfasdf'
        self.refresh_plot_needed=True

    def _get_refresh_group(self):
        return HGroup(icon_button_editor('refresh_plot', 'chart_curve_go'),
                      spring,
                      Item('auto_refresh', label='Auto Refresh'))
    # ==============================================================================
    # persistence
    #===============================================================================
    def _get_dump_attrs(self):
        return ('auto_refresh',)

    def dump(self, root):
        self._dump(root)

    def _make_dir(self, root):
        if os.path.isdir(root):
            return
        else:
            self._make_dir(os.path.dirname(root))
            os.mkdir(root)

    def _dump(self, root):
        if not self.name:
            return
        p = os.path.join(root, self.name)
        #         print root, self.name
        self._make_dir(root)
        with open(p, 'w') as fp:
            d = dict()
            attrs = self._get_dump_attrs()
            for t in attrs:
                d[t] = getattr(self, t)
            try:
                pickle.dump(d, fp)
            except (pickle.PickleError, TypeError, EOFError, TraitError):
                pass

    def _load(self, root):
        p = os.path.join(root, self.name)
        if os.path.isfile(p):
            with open(p, 'r') as fp:
                try:
                    obj = pickle.load(fp)
                    self.trait_set(**obj)
                except (pickle.PickleError, TypeError, EOFError, TraitError):
                    pass

        klass = self.plot_option_klass
        name = self.plot_option_name
        if name:
            pp = next((p for p in self.aux_plots if p.name == name), None)
            if not pp:
                po = klass(height=0)
                po.trait_set(name=name, trait_change_notfiy=False)
                self.aux_plots.append(po)

    def __repr__(self):
        return self.name

#============= EOF =============================================
