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
import yaml
from pychron.envisage.tasks.pane_helpers import icon_button_editor
from pychron.processing.plotters.options.option import AuxPlotOptions
from pychron.pychron_constants import NULL_STR


class BasePlotterOptions(HasTraits):
    aux_plots = List
    name = Str
    plot_option_klass = AuxPlotOptions
    plot_option_name = None
    refresh_plot = Button
    refresh_plot_needed=Event
    auto_refresh = Bool(False)

    def __init__(self, root, clean=False, *args, **kw):
        super(BasePlotterOptions, self).__init__(*args, **kw)
        if not clean:
            self._load(root)

    def initialize(self):
        for po in self.aux_plots:
            po.initialized = True

    def dump_yaml(self):
        """
            return a yaml blob
        """
        d = dict()
        for attr in self._get_dump_attrs():
            obj=getattr(self, attr)
            if attr == 'aux_plots':
                ap=[ai.dump_yaml() for ai in obj]
                d[attr] = ap
            else:
                d[attr] = obj
        return yaml.dump(d)

    def load_yaml(self, blob):
        d=yaml.load(blob)
        for k,v in d.iteritems():
            try:
                if k=='aux_plots':
                    ap=[]
                    for vi in v:
                        if 'ylimits' in vi:
                            vi['ylimits']=tuple(vi['ylimits'])
                            vi['_has_ylimits']=True
                        if 'xlimits' in vi:
                            vi['xlimits'] = tuple(vi['xlimits'])
                            vi['_has_xlimits'] = True
                        pp=self.plot_option_klass(**vi)
                        ap.append(pp)
                    self.trait_set(**{k:ap})
                else:
                    self.trait_set(**{k: v})
            except TraitError, e:
                print e

    def get_aux_plots(self):
        return reversed([pi
                         for pi in self.aux_plots
                         if pi.name and pi.name != NULL_STR and pi.use and pi.enabled])

    def traits_view(self):
        v = View()
        return v

    def _refresh_plot_fired(self):
        self.refresh_plot_needed=True

    def _get_refresh_group(self):
        return HGroup(icon_button_editor('refresh_plot', 'chart_curve_go'),
                      spring,
                      Item('auto_refresh', label='Auto Plot'))
    # ==============================================================================
    # persistence
    #===============================================================================
    def _get_dump_attrs(self):
        return ['auto_refresh','aux_plots']

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

        self.initialize()

    def __repr__(self):
        return self.name

#============= EOF =============================================
