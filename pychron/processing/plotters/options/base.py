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
    Bool, Event, Color, Range, Int
# import apptools.sweet_pickle as pickle

# ============= standard library imports ========================
import os
import yaml
import cPickle as pickle
# ============= local library imports  ==========================
from pychron.processing.plotters.options.option import AuxPlotOptions


class BasePlotterOptions(HasTraits):
    aux_plots = List

    plot_option_klass = AuxPlotOptions
    plot_option_name = None

    name = Str
    auto_generate_title = Bool

    initialized = True
    refresh_plot_needed = Event
    _hash = None
    formatting_options = None

    bgcolor = Color
    plot_bgcolor = Color
    plot_spacing = Range(0, 50)

    padding_left = Int(100, enter_set=True, auto_set=False)
    padding_right = Int(100, enter_set=True, auto_set=False)
    padding_top = Int(100, enter_set=True, auto_set=False)
    padding_bottom = Int(100, enter_set=True, auto_set=False)
    index_attr = Str

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
        # print name, new
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
            print 'loading plotter options {}'.format(p)
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

# ============= EOF =============================================
