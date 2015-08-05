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
from datetime import datetime
from traits.api import Instance, Bool, Int
from apptools.preferences.preference_binding import bind_preference


# ============= standard library imports ========================
import os
from threading import Timer
import hashlib
import time
# ============= local library imports  ==========================
from pychron.core.helpers.logger_setup import logging_setup
from pychron.hardware.core.i_core_device import ICoreDevice
from pychron.labspy.database_adapter import LabspyDatabaseAdapter
from pychron.loggable import Loggable
from pychron.pychron_constants import SCRIPT_NAMES


def auto_connect(func):
    def wrapper(obj, *args, **kw):
        if not obj.db.connected:
            obj.connect()

        if obj.db.connected:
            with obj.db.session_ctx():
                return func(obj, *args, **kw)

    return wrapper


class LabspyClient(Loggable):
    """
    Used to add experiments and runs to the database. Used in conjunction with ExperimentPlugin
    """
    db = Instance(LabspyDatabaseAdapter)

    use_connection_status = Bool
    connection_status_period = Int

    _timer = None

    def __init__(self, bind=True, *args, **kw):
        super(LabspyClient, self).__init__(*args, **kw)
        if bind:
            self.bind_preferences()
            self.start()

    def bind_preferences(self):
        self.db.bind_preferences()
        bind_preference(self, 'use_connection_status', 'pychron.labspy.use_connection_status')
        bind_preference(self, 'connection_status_period', 'pychron.labspy.connection_status_period')

    def test_connection(self, **kw):
        return self.db.connect(**kw)

    def start(self):

        self.debug('Start Connection status timer')
        if self.application and self.use_connection_status:
            self.debug('timer started period={}'.format(self.connection_status_period))
            t = Timer(self.connection_status_period, self._connection_status, kwargs={'verbose': True})
            t.start()

    def _connection_status(self, verbose=False):
        devs = self.application.get_services(ICoreDevice)
        if verbose:
            self.debug('Connection Status. ndevs={}'.format(len(devs or ())))
        if devs:
            ts = datetime.now()
            for dev in devs:

                # remove Communicator for name. e.g SerialCommunicator to Serial
                cname = dev.communicator.__class__.__name__,
                com_name = cname[:-12]

                self.update_connection(ts, dev.name,
                                       com_name,
                                       dev.communicator.address,
                                       dev.communicator.test_connection(),
                                       verbose=verbose)

        t = Timer(self.connection_status_period, self._connection_status, kwargs={'verbose':verbose})
        t.start()

    @auto_connect
    def add_experiment(self, exp):
        # if self.db.connected:
        #     with self.db.session_ctx():
        hid = self._generate_hid(exp)
        self.db.add_experiment(name=exp.name,
                               start_time=exp.starttime,
                               system=exp.mass_spectrometer,
                               user=exp.username)
        # ExtractionDevice=exp.extract_device,
        # HashID=hid)

    @auto_connect
    def update_experiment(self, exp, err_msg):
        # if self.db.connected:
        #     with self.db.session_ctx():
        #         hid = self._generate_hid(exp)
        #         exp = self.db.get_experiment(hid)
        #         # exp.EndTime = exp.endtime
        #         # exp.State = err_msg
        hid = self._generate_hid(exp)
        exp = self.db.get_experiment(hid)

    @auto_connect
    def update_connection(self, ts, devname, com, addr, status, verbose=False):
        if verbose:
            self.debug('Setting connection status for dev={},com={},addr={},status={}'.format(devname, com,
                                                                                              addr, status))

        appname, user = self.application.name.split('-')
        self.db.set_connection(ts,
                               appname.strip(),
                               user.strip(),
            devname, com, addr, status)

    @auto_connect
    def update_status(self, **kw):
        self.debug('update status not enabled')
        return

        status = self.db.get_status()
        if not status:
            status = self.db.add_status()

        for k, v in kw.items():
            setattr(status, k, v)

    @auto_connect
    def add_run(self, run, exp):
        exp = self.db.get_experiment(self._generate_hid(exp))
        self.db.add_analysis(exp, self._run_dict(run))

    @auto_connect
    def add_measurement(self, dev, tag, val, unit):
        val = float(val)
        self.debug('adding measurement dev={} process={} value={} ({})'.format(dev, tag, val, unit))
        self.db.add_measurement(dev, tag, val, unit)

    def connect(self):
        self.warning('not connected to db {}'.format(self.db.url))
        self.db.connect()

    # @cached_property
    # def _get_db(self):
    def _db_default(self):
        return LabspyDatabaseAdapter()

    def _run_dict(self, run):

        spec = run.spec
        return {'runid': spec.runid,
                'start_time': spec.analysis_timestamp}

        d = {dbk: getattr(spec, k) for k, dbk in (('runid', 'Runid'),
                                                  ('analysis_type', 'analysis_type'),
                                                  ('analysis_timestamp', 'TimeStamp'),
                                                  ('sample', 'Sample'),
                                                  ('extract_value', 'ExtractValue'),
                                                  ('extract_units', 'ExtractUnits'),
                                                  ('duration', 'Duration'),
                                                  ('cleanup', 'Cleanup'),
                                                  ('position', 'Position'),
                                                  ('comment', 'Comment'),
                                                  ('material', 'Material'),
                                                  ('project', 'Project'),
                                                  ('state', 'State'))}

        for si in SCRIPT_NAMES:
            k = ''.join(map(str.capitalize, si.split('_')[:-1]))
            d[k] = getattr(spec, si)

        return d

    def _generate_hid(self, exp):
        md5 = hashlib.md5()
        md5.update(exp.name)
        md5.update(exp.spectrometer)
        md5.update(exp.starttime.isoformat())
        return md5.hexdigest()


# ================= testing =========================

if __name__ == '__main__':
    from random import random
    from pychron.paths import paths

    paths.build('_dev')


    # def add_runs(c, e):
    #     class Spec():
    #         def __init__(self, record_id):
    #             self.runid = record_id
    #             # self.mass_spectrometer = 'jan'
    #             # self.extract_device = 'LF'
    #             self.analysis_timestamp = datetime.now()
    #             self.state = choice(['Finished', 'Canceled', 'Failed'])
    #             self.analysis_type = "unknown"
    #             self.sample = "FC-2"
    #             self.extract_value = random() * 2
    #             self.extract_units = 'watts'
    #             self.duration = randint(100, 200)
    #             self.cleanup = randint(100, 200)
    #             self.position = randint(0, 100)
    #             self.comment = "Test comment"
    #             self.material = "sanidine"
    #             self.project = "Monitor"
    #             self.measurement_script = 'unknown400_180'
    #             self.extraction_script = 'sniffair_x1'
    #             self.post_measurement_script = 'pump_spectrometer'
    #             self.post_equilibration_script = 'pump_extraction_line'
    #
    #     class Run():
    #         def __init__(self, *args, **kw):
    #             self.spec = Spec(*args, **kw)
    #
    #     for i in range(6):
    #         c.add_run(Run('20016-{:02d}'.format(i + 1)), e)
    #
    # def add_experiment(c):
    #     class Exp():
    #         def __init__(self, name, user, status):
    #             self.name = name
    #             self.username = user
    #             spec = choice(('Jan','Obama'))
    #             self.spectrometer = spec
    #             self.mass_spectrometer = spec
    #             self.extract_device = choice(('Fusions CO2', 'Fusions Diode'))
    #             self.status = status
    #             self.starttime = datetime.now()
    #
    #     e = Exp('Current Experiment', 'foobar', 'Running')
    #     c.add_experiment(e)
    #     return e
    #
    # def update_status(c):
    #     c.update_status(Error='Error big time')
    #     c.update_status(Message='This is a long message', ShortMessage='This is a short message')

    def add_measurements(c):
        for i in range(100):
            c.add_measurement('AirPressure', 'pneumatics', random(), 'PSI')
            c.add_measurement('Environmental', 'temperature', random() * 2 + 70, 'C')
            c.add_measurement('Environmental', 'humidity', random() * 5 + 50, '%')

            time.sleep(1)


    logging_setup('labspyclient', use_archiver=False)
    # c = LabspyClient(bind=False, host='129.138.12.138', port=27017)
    # c = MeteorLabspyClient(bind=False, host='localhost', port=3001)
    # # update_state(c)
    # for i in range(10):
    # add_device(c)
    # time.sleep(1)

    clt = LabspyClient(bind=False)
    clt.db.host = 'localhost'
    clt.db.username = os.environ.get('DB_USER')
    clt.db.password = os.environ.get('DB_PWD')
    clt.db.name = 'labspy'
    clt.test_connection()

    # set status
    # update_status(clt)

    # measurements
    add_measurements(clt)

    # experiments/runs
    # exp = add_experiment(clt)
    # add_runs(clt, exp)
# ============= EOF =============================================
# class MeteorLabspyClient(LabspyClient):
# host = Str
#     port = Int
#     database_name = Str
#
#     _client = None
#
#     def __init__(self, *args, **kw):
#         super(MeteorLabspyClient, self).__init__(*args, **kw)
#         self.database_name = 'meteor'
#
#     def bind_preferences(self):
#         bind_preference(self, 'host', 'pychron.labspy.host')
#         bind_preference(self, 'port', 'pychron.labspy.port')
#         bind_preference(self, 'database_name', 'pychron.labspy.database_name')
#
#     def test_connection(self, warn=True):
#         if self.host and self.port:
#             from pymongo import MongoClient
#             from pymongo.errors import ConnectionFailure
#
#             url = 'mongodb://{}:{}/'.format(self.host, self.port)
#             try:
#                 self._client = MongoClient(url)
#                 return True
#             except ConnectionFailure:
#                 if warn:
#                     self.warning_dialog('failed connecting to database at {}'.format(url))
#         return False
#
#     def add_experiment(self, exp):
#         db = self.db
#         if db:
#             now = datetime.now()
#             attrs = ('username', 'extract_device', 'mass_spectrometer', 'name', 'status')
#             doc = {ai: getattr(exp, ai) for ai in attrs}
#
#             hid = self._generate_hid(exp)
#             doc.update(**{'starttime': time.mktime(exp.starttime.timetuple()),
#                           'timestamp': time.mktime(now.timetuple()),
#                           'hash_id': hid})
#
#             db.experiments.insert(doc)
#             # exp.hash_id = hid
#
#     def update_experiment(self, exp, err_msg):
#         if self.db:
#             db = self.db
#             hid = self._generate_hid(exp)
#             doc = db.experiments.find_one({'hash_id': hid})
#             if doc:
#                 db.experiments.update({'_id': doc['_id']},
#                                       {'$set': {'status': err_msg or 'Finished',
#                                                 'timestampf': time.mktime(datetime.now().timetuple())}})
#
#     def update_status(self, **kw):
#         db = self.db
#         if db:
#             doc = db.state.find_one({})
#             if not doc:
#                 doc \
#                     = kw
#                 db.state.insert(doc)
#             else:
#                 db.state.update({'_id': doc['_id']}, {'$set': kw})
#
#     def _generate_hid(self, exp):
#         md5 = hashlib.md5()
#         md5.update(exp.name)
#         md5.update(exp.spectrometer)
#         md5.update(exp.starttime.isoformat())
#         return md5.hexdigest()
#
#     def add_run(self, run, exp):
#         db = self.db
#         if db:
#             # attrs = ('record_id', 'timestamp', 'experiment_name', 'state')
#             # doc = {k: getattr(run, k) for k in attrs}
#             doc = self._make_run_doc(run, exp)
#             db.runs.insert(doc)
#
#     def add_device_post(self, devs):
#         # clt = self._client
#         # if not clt:
#         # return
#         #
#         # db = clt[self.database_name]
#
#         db = self.db
#         if db:
#             now = datetime.now()
#             # print now.isoformat(), now.strftime('%H:%M:%S')
#             doc = {  # 'timestamp': now,
#                      # 'timestampt': now.strftime('%H:%M:%S'),
#                      'timestamp': time.mktime(now.timetuple())}
#
#             values = []
#             for di in devs:
#                 for vk, cv, ui in zip(di.value_keys, di.current_values, di.units):
#                     values.append({'device': di.name,
#                                    'name': vk,
#                                    'value': cv,
#                                    'units': ui})
#
#             doc['values'] = values
#
#             # pprint(doc, width=4)
#             db.devices.insert(doc)
#
#     # private
#     def _make_run_doc(self, run, exp):
#         spec = run.spec
#
#         d = {k: getattr(spec, k) for k in ('runid',
#                                            'analysis_type',
#                                            'sample',
#                                            'extract_value',
#                                            'duration',
#                                            'cleanup',
#                                            'position',
#                                            'comment',
#                                            'material',
#                                            'project',
#                                            'mass_spectrometer',
#                                            'extract_device',
#                                            'state')}
#
#         d['experiment_name'] = exp.name
#         if spec.analysis_timestamp:
#             d['timestamp'] = time.mktime(spec.analysis_timestamp.timetuple())
#             # d['date'] = spec.analysis_timestamp.strftime('%m/%d/%Y %I:%M:%S %p')
#             # d['runtime'] = spec.analysis_timestamp.strftime('%I:%M:%S %p')
#         else:
#             d['date'] = ''
#             d['timestamp'] = ''
#             d['runtime'] = ''
#
#         for si in SCRIPT_NAMES:
#             d[si] = getattr(spec, si)
#
#         return d
#
#     def _get_property(self):
#         if self._client:
#             return self._client[self.database_name]
#
#
# def add_device(clt):
#     class Dev():
#         def __init__(self, name, values, units):
#             self.name = name
#             self.units = units
#             self.value_keys = values
#             self.current_values = [random() for k in values]
#
#
#     a = Dev('pneumatic', ('pressure',), ('torr',))
#     b = Dev('environment',
#             ('temperature', 'humidity'), ('C', '%'))
#     c = Dev('gauge', ('bone_ig',), ('torr',))
#     d = Dev('gauge', ('microbone_ig',), ('torr',))
#     clt.add_device_post([a, b, c, d])
