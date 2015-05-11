# ===============================================================================
# Copyright 2013 Jake Ross
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
import hashlib

from traits.api import HasTraits, List, Str, TraitError, \
    Button, Bool, Event, Color, Range, String, Int, on_trait_change
from traitsui.api import View, HGroup, spring, VGroup, Item, Group, Spring
# import apptools.sweet_pickle as pickle

# ============= standard library imports ========================
import os
import yaml
import cPickle as pickle
# ============= local library imports  ==========================
from pychron.envisage.icon_button_editor import icon_button_editor
from pychron.processing.plotters.options.option import AuxPlotOptions
from pychron.pychron_constants import NULL_STR


class BasePlotterOptions(HasTraits):
    aux_plots = List
    name = Str
    initialized = True
    refresh_plot_needed = Event
    _hash = None
    formatting_options = None

    def __init__(self, root, clean=False, *args, **kw):
        super(BasePlotterOptions, self).__init__(*args, **kw)
        if not clean:
            self._load(root)

    def set_aux_plot_height(self, name, height):
        plot = next((ai for ai in self.aux_plots
                     if ai.name == name), None)
        if plot:
            plot.height = height

    def load(self, root):
        self._load(root)

    def load_factory_defaults(self, path):
        with open(path, 'r') as rfile:
            yd = yaml.load(rfile)
            self._load_factory_defaults(yd)

    def dump(self, root):
        self._dump(root)

    def get_formatting_value(self, attr, oattr=None):
        """
        retrieve either a value from the formatting_options object or from the plotter_options object
        use formatting_options first and if it exists
        any subsequent refreshes check if plotter_options has changed if so use its values

        :param attr: FormattingOptions attribute
        :param oattr: PlotterOptions attribute
        :return: formatting value
        """
        if oattr is None:
            oattr = attr

        if self.formatting_options is None:
            v = getattr(self, oattr)
        else:
            if self.has_changes():
                v = getattr(self, oattr)
            else:
                v = getattr(self.formatting_options, attr)

        return v

    def get_hash(self):
        attrs = self._get_change_attrs()

        h = hashlib.md5()
        for ai in attrs:
            h.update('{}{}'.format(ai, (getattr(self, ai))))
        return h.hexdigest()

    def set_hash(self):
        self._hash = self.get_hash()

    def has_changes(self):
        return self._hash and self._hash != self.get_hash()

    # handlers
    def _anytrait_changed(self, name, new):
        print name, new
        if name in self._get_refreshable_attrs():
            if self._process_trait_change(name, new):
                self.refresh_plot_needed = True

    # private
    def _process_trait_change(self, name, new):
        return True

    def _get_refreshable_attrs(self):
        return []

    def _make_dir(self, root):
        if os.path.isdir(root):
            return
        else:
            self._make_dir(os.path.dirname(root))
            os.mkdir(root)

    def _get_change_attrs(self):
        raise NotImplementedError

    def _get_dump_attrs(self):
        raise NotImplementedError

    def _dump(self, root):
        if not self.name:
            return
        p = os.path.join(root, self.name)
        # print root, self.name
        self._make_dir(root)
        with open(p, 'w') as wfile:
            d = dict()
            attrs = self._get_dump_attrs()
            for t in attrs:
                d[t] = v = getattr(self, t)

            try:
                pickle.dump(d, wfile)
            except (pickle.PickleError, TypeError, EOFError, TraitError), e:
                print 'error dumping {}'.format(self.name), e

    def _load(self, root):
        p = os.path.join(root, self.name)
        if os.path.isfile(p):
            with open(p, 'r') as rfile:
                try:
                    obj = pickle.load(rfile)
                    self.trait_set(**obj)
                except (pickle.PickleError, TypeError, EOFError, TraitError), e:
                    print 'error loading {}'.format(self.name), e
        self._load_hook()

    def _load_hook(self):
        pass

    def _load_factory_defaults(self, yd):
        raise NotImplementedError

    def __repr__(self):
        return self.name


class FigurePlotterOptions(BasePlotterOptions):
    plot_option_klass = AuxPlotOptions
    plot_option_name = None

    include_legend = Bool(False)
    refresh_plot = Button
    # refresh_plot_needed = Event

    auto_refresh = Bool(False)
    auto_generate_title = Bool(False)
    index_attr = String

    bgcolor = Color
    plot_bgcolor = Color
    plot_spacing = Range(0, 50)

    padding_left = Int(100, enter_set=True, auto_set=False)
    padding_right = Int(100, enter_set=True, auto_set=False)
    padding_top = Int(100, enter_set=True, auto_set=False)
    padding_bottom = Int(100, enter_set=True, auto_set=False)

    use_xgrid = Bool(True)
    use_ygrid = Bool(True)

    def deinitialize(self):
        for po in self.aux_plots:
            po.initialized = False

    def initialize(self):
        for po in self.aux_plots:
            po.initialized = True

    def dump_yaml(self):
        """
            return a yaml blob
        """
        d = dict()
        for attr in self._get_dump_attrs():
            obj = getattr(self, attr)
            if attr == 'aux_plots':
                ap = [ai.dump_yaml() for ai in obj]
                d[attr] = ap
            else:
                d[attr] = obj
        return yaml.dump(d)

    def load_yaml(self, blob):
        d = yaml.load(blob)
        for k, v in d.iteritems():
            try:
                if k == 'aux_plots':
                    ap = []
                    for vi in v:
                        if 'ylimits' in vi:
                            vi['ylimits'] = tuple(vi['ylimits'])
                            vi['_has_ylimits'] = True
                        if 'xlimits' in vi:
                            vi['xlimits'] = tuple(vi['xlimits'])
                            vi['_has_xlimits'] = True
                        pp = self.plot_option_klass(**vi)
                        ap.append(pp)
                    self.trait_set(**{k: ap})
                else:
                    self.trait_set(**{k: v})
            except TraitError, e:
                print 'exception', e

    def get_aux_plots(self):
        return reversed([pi
                         for pi in self.aux_plots
                         if pi.name and pi.name != NULL_STR and pi.use and pi.enabled])

    def traits_view(self):
        v = View()
        return v

    def _refresh_plot_fired(self):
        self.refresh_plot_needed = True

    def _get_refresh_group(self):
        """
         disabled auto_refresh. causing a max recursion depth error. something to do with persisted xlimits
        """
        return HGroup(icon_button_editor('refresh_plot', 'refresh',
                                         tooltip='Refresh plot'))

    def _get_padding_group(self):
        return VGroup(HGroup(Spring(springy=False, width=100),
                             Item('padding_top', label='Top'),
                             spring, ),
                      HGroup(Item('padding_left', label='Left'),
                             Item('padding_right', label='Right')),
                      HGroup(Spring(springy=False, width=100), Item('padding_bottom', label='Bottom'),
                             spring),
                      enabled_when='not formatting_options',
                      label='Padding', show_border=True)

    def _get_bg_group(self):
        grp = Group(Item('bgcolor', label='Figure'),
                    Item('plot_bgcolor', label='Plot'),
                    show_border=True,
                    enabled_when='not formatting_options',
                    label='Background')
        return grp

    # ==============================================================================
    # persistence
    # ===============================================================================
    def _get_dump_attrs(self):
        return ['auto_refresh', 'aux_plots',
                'bgcolor', 'plot_bgcolor',
                'plot_spacing',
                'padding_left',
                'padding_right',
                'padding_top',
                'padding_bottom',
                'use_xgrid', 'use_ygrid']

    def _load_hook(self):
        klass = self.plot_option_klass
        name = self.plot_option_name
        if name:

            pp = next((p for p in self.aux_plots if p.name == name), None)
            if not pp:
                po = klass(height=0)
                po.trait_set(name=name,
                             use=True,
                             trait_change_notfiy=False)
                self.aux_plots.append(po)

        self.initialize()

    def _load_factory_defaults(self, yd):
        padding = yd.get('padding')
        if padding:
            self.trait_set(**padding)

        self._set_defaults(yd, 'axes', ('xtick_in', 'xtick_out',
                                        'ytick_in', 'ytick_out',
                                        'use_xgrid', 'use_ygrid'))

        self._set_defaults(yd, 'background', ('bgcolor',
                                              'plot_bgcolor'))

    def _set_defaults(self, yd, name, attrs):
        d = yd.get(name)
        if d:
            for attr in attrs:
                try:
                    setattr(self, attr, d[attr])
                except KeyError, e:
                    print d, attr

    @on_trait_change('use_xgrid, use_ygrid, padding+, bgcolor, plot_bgcolor')
    def _refresh_handler(self):
        self.refresh_plot_needed = True

# ============= EOF =============================================
