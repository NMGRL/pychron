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
from traits.api import HasTraits, Str, Int, Bool, Any, Float, Property, on_trait_change
from traitsui.api import View, UItem, Item, HGroup, VGroup
# ============= standard library imports ========================
import os
import pickle
from uncertainties import nominal_value, std_dev
import yaml
from numpy import array
# ============= local library imports  ==========================
from pychron.loggable import Loggable
from pychron.paths import paths


class SystemHealthSeries(Loggable):
    _limit = 100
    _values = None

    def __init__(self, *args, **kw):
        super(SystemHealthSeries, self).__init__(*args, **kw)
        self._load()

    def add_analysis(self, an):
        """
        add an automated run to the system health series.
        configure which values are saved to the series
        with setupfiles/system_health.yaml.

        data written to .hidden/health_series.yaml

        analyze the series and check for any conditions that should stop the
        experiment
        :param an: Automated Run
        :return: 'cancel' or 'terminate'
        """

        try:
            p = os.path.join(paths.hidden_dir, 'health_series.yaml')
            if os.path.isfile(p):
                with open(p, 'r') as fp:
                    series = yaml.load(fp)
            else:
                series = []

            d = self._make_analysis_dict(an)
            if d:
                series.append(d)
                nseries = series[-self._limit:]
                with open(p, 'w') as fp:
                    yaml.dump(nseries, fp)
        except BaseException, e:
            self.warning('system health add_analysis failed. error="{}"'.format(e))

        return self._analyze_series(nseries)

    def _analyze_series(self, series):
        """
        iterate the conditionals
        return 'cancel' or 'terminate'
        cancel: stop experiment
        terimate: stop run

        :param series: list of dicts
        :return:
        """
        for ci in self._conditionals:
            ret = self._execute_conditional(ci, series)
            if ret:
                return ret

    def _execute_conditional(self, cond, series):
        ret = None
        attr = cond['attribute']
        comp = cond['comparison']
        func = cond['function']
        if func not in ['std', 'mean']:
            self.debug('invalid function. "{}"'.format(func))
            return

        x = array([si[attr] for si in series])
        if func == 'std':
            x = x.std()
        elif func == 'mean':
            x = x.mean()

        if eval(comp, {'x': x}):
            ret = cond['action']

        return ret

    def _load(self):
        p = os.path.join(paths.setup_dir, 'system_health.yaml')
        with open(p, 'r') as fp:
            config = yaml.load(fp)
            self._values = config['values']
            self._limit = config['general']['limit']
            self._conditionals = config['conditionals']

    def _make_analysis_dict(self, an):
        arar = an.arar_age
        try:
            d = {}
            for v in self._values:
                vv = arar.get_value(v)
                d[v] = nominal_value(vv)
                d['{}_err'.format(v)] = std_dev(vv)

        except BaseException, e:
            self.warning('failed making system health analysis dict. error="{}"'.format(e))

        return d

# ============= EOF =============================================



