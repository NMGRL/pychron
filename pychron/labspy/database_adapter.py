# ===============================================================================
# Copyright 2014 Jake Ross
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
from apptools.preferences.preference_binding import bind_preference
from traits.api import HasTraits, Button
from traitsui.api import View, Item
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.database.core.database_adapter import DatabaseAdapter
from pychron.labspy.orm import Measurement, ProcessInfo, Device, Version, Status, Experiment, Analysis, AnalysisType


class LabspyDatabaseAdapter(DatabaseAdapter):
    kind = 'mysql'

    def bind_preferences(self):
        bind_preference(self, 'host', 'pychron.labspy.host')
        bind_preference(self, 'port', 'pychron.labspy.port')
        bind_preference(self, 'password', 'pychron.labspy.password')
        bind_preference(self, 'name', 'pychron.labspy.name')

    def add_experiment(self, **kw):
        exp = Experiment(**kw)
        return self._add_item(exp)

    def add_analysis(self, dbexp, rd):
        at = None
        if 'analysis_type' in rd:
            analysis_type = rd.pop('analysis_type')
            at = self.get_analysis_type(analysis_type)
            if not at:
                at = self.add_analysis_type(analysis_type)
        an = Analysis(**rd)
        if at:
            an.analysis_type = at

        an.experiment = dbexp
        return self._add_item(an)

    def update_experiment(self, hashid, **kw):
        exp = self.get_experiment(hashid)
        for k, v in kw.items():
            setattr(exp, k, v)

    def add_device(self, dev):
        dev = Device(Name=dev)
        return self._add_item(dev)

    def add_measurement(self, dev, name, value, unit):
        pinfo = self.get_process_info(dev, name)
        if not pinfo:
            pinfo = self.add_process_info(dev, name, unit)

        measurement = Measurement(Value=value)
        measurement.process = pinfo
        return self._add_item(measurement)

    def add_process_info(self, dev, name, unit):
        self.debug('add process info {} {} {}'.format(dev, name, unit))
        dbdev = self.get_device(dev)
        if not dbdev:
            self.debug('add device {}'.format(dev))
            dbdev = self.add_device(dev)

        p = ProcessInfo(Name=name, Units=unit)
        p.device = dbdev
        return self._add_item(p)

    def add_status(self):
        p = Status()
        return self._add_item(p)

    def add_analysis_type(self, name):
        obj = AnalysisType(Name=name)
        return self._add_item(obj)

    # getters
    def get_analysis_type(self, name):
        return self._retrieve_item(AnalysisType, name, key='Name')

    def get_experiment(self, hid):
        return self._retrieve_item(Experiment, hid, key='HashID')

    def get_status(self):
        with self.session_ctx() as sess:
            q = sess.query(Status)
            return self._query_one(q)

    def get_migrate_version(self, **kw):
        with self.session_ctx() as sess:
            q = sess.query(Version)
            mv = q.one()
            return mv

    def get_device(self, name):
        return self._retrieve_item(Device, name, key='Name')

    def get_process_info(self, dev, name):
        dev = self.get_device(dev)
        if dev:
            return next((p for p in dev.processes if p.Name == name), None)

# ============= EOF =============================================



