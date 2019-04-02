# ===============================================================================
# Copyright 2017 ross
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

import six
from traits.api import HasTraits, List, Str, Float, Int
from traitsui.api import View, HGroup, Item

from pychron.core.ui.color_map_bar_editor import BarGaugeEditor


class BaseGauge(HasTraits):
    name = Str
    pressure = Float
    display_name = Str
    low = 5e-10
    high = 1e-8
    color_scalar = 1
    width = Int(100)
    channel = Str

    def traits_view(self):
        v = View(HGroup(Item('display_name', show_label=False, style='readonly',
                             width=-30, ),
                        Item('pressure',
                             format_str='%0.2e',
                             show_label=False,
                             style='readonly'),
                        Item('pressure',
                             show_label=False,
                             width=self.width,
                             editor=BarGaugeEditor(low=self.low,
                                                   high=self.high,
                                                   scale='power',
                                                   color_scalar=self.color_scalar,
                                                   width=self.width))))
        return v


class BaseGaugeController(HasTraits):
    address = Str
    gauges = List
    display_name = Str
    gauge_klass = BaseGauge

    scan_func = 'update_pressures'

    def update_pressures(self, verbose=False):
        if verbose:
            self.debug('update pressures')

        resps = [self._update_pressure(g, verbose) for g in self.gauges]
        return any(resps)

    def get_gauge(self, name):
        return next((gi for gi in self.gauges
                     if gi.name == name or gi.display_name == name), None)

    def get_pressure(self, gauge, force=False, verbose=False):
        if isinstance(gauge, (str, six.text_type)):
            gauge = self.get_gauge(gauge)
        if gauge is not None:
            if force:
                self._update_pressure(gauge.name, verbose)

            return gauge.pressure

    def get_pressures(self, force=False):
        if force:
            self.update_pressures()

        return [g.pressure for g in self.gauges]

    def _pressure_change(self, obj, name, old, new):
        self.trait_set(**{'{}_pressure'.format(obj.name): new})

    def _read_pressure(self, *args, **kw):
        raise NotImplementedError

    def _set_gauge_pressure(self, gauge, v):
        if isinstance(gauge, (str, six.text_type)):
            gauge = self.get_gauge(gauge)

        if gauge is not None:
            try:
                gauge.pressure = float(v)
                return True
            except (TypeError, ValueError):
                pass

    def _get_pressure(self, name, verbose=False, force=False):
        if self._scanning and not force:
            attr = '{}_pressure'.format(name)
            if hasattr(self, attr):
                return getattr(self, attr)

        return self._read_pressure(name, verbose)

    def _update_pressure(self, gauge, verbose=False):
        print(gauge, type(gauge))
        if isinstance(gauge, str):
            gauge = self.get_gauge(gauge)

        if gauge:
            p = self._read_pressure(gauge, verbose)
            if self._set_gauge_pressure(gauge, p):
                return True

    def _load_gauges(self, config, *args, **kw):
        ns = self.config_get(config, 'Gauges', 'names')
        if ns:
            ans = self.config_get(config, 'Gauges', 'display_names', optional=True)
            if not ans:
                ans = ns

            lows = self.config_get(config, 'Gauges', 'lows', optional=True, default='1e-10, 1e-3, 1e-3')
            highs = self.config_get(config, 'Gauges', 'highs', optional=True, default='1e-6, 1, 1')
            cs = self.config_get(config, 'Gauges', 'color_scalars', optional=True, default='1, 1, 1')
            chs = self.config_get(config, 'Gauges', 'channels', optional=True, default='1, 2, 3')

            for gi in zip(*[x.split(',') for x in (ns, ans, lows, highs, cs, chs)]):
                # ni, ai, li, hi, ci, cn = list(map(str.strip, gi))
                ni, ai, li, hi, ci, cn = [gg.strip() for gg in gi]

                g = self.gauge_klass(name=ni, display_name=ai, channel=cn)
                try:
                    g.low = float(li)
                except ValueError as e:
                    self.warning_dialog('Invalid lows string. {}'.format(e), title=self.config_path)
                    continue

                try:
                    g.high = float(hi)
                except ValueError as e:
                    self.warning_dialog('Invalid highs string. {}'.format(e), title=self.config_path)
                    continue
                try:
                    g.color_scalar = int(ci)
                except ValueError as e:
                    self.warning_dialog('Invalid color_scalar string. {}'.format(e), title=self.config_path)
                    continue

                p = '{}_pressure'.format(ni)
                self.add_trait(p, Float)
                g.on_trait_change(self._pressure_change, 'pressure')

                self.gauges.append(g)
# ============= EOF =============================================
