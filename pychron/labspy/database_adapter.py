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
from datetime import datetime, timedelta

from apptools.preferences.preference_binding import bind_preference
# ============= standard library imports ========================
# ============= local library imports  ==========================
from sqlalchemy import and_
from sqlalchemy.exc import SQLAlchemyError

from pychron.database.core.database_adapter import DatabaseAdapter
from pychron.labspy.orm import Measurement, ProcessInfo, Version, \
    Device, Experiment, Analysis, Connections  # , Version, Status, Experiment, Analysis, AnalysisType


class LabspyDatabaseAdapter(DatabaseAdapter):
    kind = 'mysql'

    def bind_preferences(self):
        bind_preference(self, 'host', 'pychron.labspy.host')
        # bind_preference(self, 'port', 'pychron.labspy.port')
        bind_preference(self, 'username', 'pychron.labspy.username')
        bind_preference(self, 'password', 'pychron.labspy.password')
        bind_preference(self, 'name', 'pychron.labspy.name')

    def add_experiment(self, **kw):
        exp = Experiment(**kw)
        return self._add_item(exp)

    def add_analysis(self, dbexp, rd):
        at = None
        # if 'analysis_type' in rd:
        #     analysis_type = rd.pop('analysis_type')
        #     at = self.get_analysis_type(analysis_type)
        #     if not at:
        #         at = self.add_analysis_type(analysis_type)

        an = Analysis(**rd)
        if at:
            an.analysis_type = at

        an.experiment = dbexp
        return self._add_item(an)

    def set_connection(self, ts, appname, username, devname, com, addr, status):
        try:
            conn = self.get_connection(appname, devname)
        except SQLAlchemyError, e:
            self.warning('Error getting connection {}.{} exception: {}'.format(appname, devname, e))
            return

        if conn is None:
            conn = Connections()
            self._add_item(conn)

        conn.appname = appname
        conn.username = username
        conn.devname = devname
        conn.com = com
        conn.address = addr
        conn.status = bool(status)
        conn.timestamp = ts

    def get_connection(self, appname, devname):
        q = self.session.query(Connections)
        q = q.filter(and_(Connections.appname == appname, Connections.devname == devname))
        return self._query_first(q, reraise=True)

    def update_experiment(self, hashid, **kw):
        exp = self.get_experiment(hashid)
        for k, v in kw.items():
            setattr(exp, k, v)

    def add_device(self, dev):
        dev = Device(name=dev)
        return self._add_item(dev)

    def add_measurement(self, dev, name, value, unit):
        pinfo = self.get_process_info(dev, name)
        # if not pinfo:
        #     pinfo = self.add_process_info(dev, name, unit)
        if pinfo:
            measurement = Measurement(value=value)
            measurement.process = pinfo
            return self._add_item(measurement)
        else:
            self.warning('ProcessInfo={} Device={} not available'.format(name, dev))

    def add_process_info(self, dev, name, unit):
        self.debug('add process info {} {} {}'.format(dev, name, unit))
        dbdev = self.get_device(dev)
        if not dbdev:
            self.debug('add device {}'.format(dev))
            dbdev = self.add_device(dev)

        p = ProcessInfo(name=name, units=unit)
        p.device = dbdev
        return self._add_item(p)

    # def add_status(self):
    #     p = Status()
    #     return self._add_item(p)
    #
    # def add_analysis_type(self, name):
    #     obj = AnalysisType(Name=name)
    #     return self._add_item(obj)

    # getters
    # def get_analysis_type(self, name):
    #     return self._retrieve_item(AnalysisType, name, key='Name')
    #
    # def get_experiment(self, hid):
    #     return self._retrieve_item(Experiment, hid, key='HashID')
    #
    # def get_status(self):
    #     with self.session_ctx() as sess:
    #         q = sess.query(Status)
    #         return self._query_one(q)

    def get_migrate_version(self, **kw):
        q = self.session.query(Version)
        q = q.limit(1)
        mv = q.one()
        return mv

    def get_device(self, name):
        return self._retrieve_item(Device, name, key='name')

    def get_process_info(self, dev, name):
        q = self.session.query(ProcessInfo)
        q = q.join(Device)
        q = q.filter(Device.name == dev)
        q = q.filter(ProcessInfo.name == name)
        return self._query_one(q)

    def get_latest_lab_temperatures(self):
        return self._get_latest('Temp.')

    def get_latest_lab_humiditys(self):
        return self._get_latest('Hum.')

    def get_latest_lab_pneumatics(self):
        return self._get_latest('Pressure')

    def _get_latest(self, tag):
        values = []
        with self.session_ctx(use_parent_session=False) as sess:
            q = sess.query(ProcessInfo)
            q = q.filter(ProcessInfo.name.contains(tag))
            ps = self._query_all(q)

            for p in ps:
                q = sess.query(Measurement)
                q = q.filter(Measurement.process_info_id == p.id)
                q = q.filter(Measurement.pub_date > datetime.now() - timedelta(hours=24))
                q = q.order_by(Measurement.pub_date.desc())

                record = self._query_first(q)
                if record:
                    values.append({'name': p.name,
                                   'title': p.graph_title,
                                   'pub_date': record.pub_date.isoformat(),
                                   'value': record.value,
                                   'device': p.device.name})

        return values

    def get_measurements(self, device, name, low=None, high=None):
        q = self.session.query(Measurement)
        q = q.join(ProcessInfo, Device)
        q = q.filter(Device.name == device)
        q = q.filter(ProcessInfo.name == name)

        if low:
            q = q.filter(Measurement.pub_date >= low)

        return self._query_all(q)

# ============= EOF =============================================
