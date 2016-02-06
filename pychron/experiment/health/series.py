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
import shutil
import time
# ============= standard library imports ========================
import os
from uncertainties import nominal_value, std_dev
import yaml
from numpy import array, diff, where
# ============= local library imports  ==========================
from pychron.core.helpers.filetools import unique_path2
from pychron.loggable import Loggable
from pychron.paths import paths


def reset_system_health_series():
    src = os.path.join(paths.hidden_dir, 'health_series.yaml')
    if os.path.isfile(src):
        dest, _ = unique_path2(paths.hidden_dir, 'health_series', extension='.yaml')
        shutil.copyfile(src, dest)
        os.remove(src)


class SystemHealthSeries(Loggable):
    """
    Maintain a series of analyses.
    Provides an interface to check conditionals and cancel/terminate if conditional evaluates to true.
    For example you can check to make sure the standard deviation of the last N airs is less than
    and threshold value.

    configuration and definition of conditionals is located in setupfiles/system_health.yaml
    """
    _limit = 100
    _values = None

    def __init__(self, *args, **kw):
        super(SystemHealthSeries, self).__init__(*args, **kw)
        self._load()

    def reset(self):
        """
            backup and erase the current health_series.yaml file

        :return:
        """
        reset_system_health_series()

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
            for iso in an.isotopes.values():
                if self.isotope_health.check(iso):
                    self._flag_analysis(an, iso.name)

        except BaseException, e:
            self.warning('isotope health add_analysis failed. error="{}"'.format(e))

        try:
            nseries = self._add_yaml(an)
            return self._analyze_series(nseries)
        except BaseException, e:
            self.warning('system health add_analysis failed. error="{}"'.format(e))

    # private
    def _flag_analysis(self, an, name):
        self.info('FLAG ---- Analysis: {}, isotope: {}'.format(an.record_id, name))

    def _add_yaml(self, an):
        p = os.path.join(paths.hidden_dir, 'health_series.yaml')
        if os.path.isfile(p):
            with open(p, 'r') as rfile:
                series = yaml.load(rfile)
        else:
            series = []

        d = self._make_analysis_dict(an)
        if d:
            series.append(d)
            series = series[-self._limit:]
            with open(p, 'w') as wfile:
                yaml.dump(series, wfile)

        return series

    def _analyze_series(self, series):
        """
        iterate the conditionals
        return 'cancel' or 'terminate'
        cancel: stop experiment
        terimate: stop run

        :param series: list of dicts
        :return:
        """
        # bin series by analysis time
        # only analyze the last bin
        ts = array([si['timestamp'] for si in series])
        ds = diff(ts)

        # tolerance_seconds = 60 * 60 * self._bin_hours
        # ds = diff(ts) > tolerance_seconds
        # bounds = where(ds)[0]
        # itemidx = bounds[-1] if bounds else 0
        # series = series[itemidx:]

        for ci in self._conditionals:
            ret = self._execute_conditional(ci, series, ds)
            if ret:
                return ret

    def _execute_conditional(self, cond, series, ds):
        """
        evaluate conditional with series as concept
        conditionals defined in system_health.yaml

        std - standard deviation
        mean- mean
        value - check if the latest value is different from the previous

        :param cond: dict
        :param series: list of dicts
        :param ds: result of np.diff
        :return: None, 'cancel', 'terminate'
        """

        ret = None
        func = cond['function']
        if func not in ['std', 'mean', 'value']:
            self.debug('invalid function. "{}"'.format(func))
            return

        attr = cond['attribute']
        action = cond.get('action', 'cancel')
        atypes = cond.get('analysis_types', None)
        bin_hours = cond.get('bin_hours', 6)

        tolerance_seconds = 60 * 60 * bin_hours
        dd = ds > tolerance_seconds
        bounds = where(dd)[0]
        itemidx = bounds[-1] if bounds else 0

        if atypes:
            series = [si for si in series if si['analysis_type'] in atypes]

        series_v = [si[attr] for si in series[itemidx:] if attr in si]

        if func == 'value':
            if series_v[-1] != series_v[-2]:
                ret = action
        else:
            minx = cond.get('min_n', 10)
            if len(series) <= minx:
                return

            x = array(series_v)
            if func == 'std':
                x = x.std()
            elif func == 'mean':
                x = x.mean()

            comp = cond['comparison']
            if eval(comp, {'x': x}):
                ret = action

        return ret

    def _load(self):
        """
        load system_health.yaml file.
        this file defines multiple configuration values
        :return:
        """
        p = os.path.join(paths.setup_dir, 'system_health.yaml')
        if os.path.isfile(p):
            with open(p, 'r') as rfile:
                config = yaml.load(rfile)
                if config:
                    self._values = config['values']
                    self._conditionals = config['conditionals']

                    general = config['general']
                    self._limit = general['limit']

    def _make_analysis_dict(self, an):
        """
        make a dictionary from this automated run.

        value keys are defined in system_health.yaml
        :param an: AutomatedRun
        :return: dict
        """

        ig = an.isotope_group
        try:
            spec = an.spec
            d = {'identifier': spec.identifier,
                 'aliquot': spec.aliquot,
                 'step': spec.step,
                 'analysis_type': spec.analysis_type,
                 'runid': spec.runid,
                 'uuid': spec.uuid,
                 'timestamp': time.mktime(spec.analysis_timestamp.timetuple())}

            spec_dict = an.persister.per_spec.spec_dict
            defl_dict = an.persister.per_spec.defl_dict

            for v in self._values:
                if v.endswith('_deflection'):
                    try:
                        k, _ = v.split('_')
                        d[v] = defl_dict[k]
                        continue
                    except KeyError:
                        pass
                else:
                    try:
                        d[v] = spec_dict[v]
                    except KeyError:
                        vv = ig.get_value(v)
                        d[v] = nominal_value(vv)
                        d['{}_err'.format(v)] = std_dev(vv)

        except BaseException, e:
            self.warning('failed making system health analysis dict. error="{}"'.format(e))

        return d


# ============= EOF =============================================



