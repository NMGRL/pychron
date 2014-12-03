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
import hashlib
from pprint import pprint
import time
from apptools.preferences.preference_binding import bind_preference
from traits.api import HasTraits, Button, Str, Int
from traitsui.api import View, Item
# ============= standard library imports ========================
from pymongo import MongoClient
# ============= local library imports  ==========================
from pychron.loggable import Loggable
from pychron.pychron_constants import SCRIPT_NAMES


class LabspyClient(Loggable):
    host = Str
    port = Int
    database_name = Str('meteor')
    _client = None

    def __init__(self, bind=True, *args, **kw):
        super(LabspyClient, self).__init__(*args, **kw)
        if bind:
            bind_preference(self, 'host', 'pychron.labspy.host')
            bind_preference(self, 'port', 'pychron.labspy.port')

        if self.host and self.port:
            self._client = MongoClient('mongodb://{}:{}/'.format(self.host, self.port))
            # self._client = MongoClient('mongodb://{}/'.format(self.host))

    @property
    def db(self):
        return self._client[self.database_name]

    def add_experiment(self, exp):
        db = self.db
        now = datetime.now()
        attrs = ('username', 'extract_device', 'mass_spectrometer', 'name', 'status')
        doc = {ai: getattr(exp, ai) for ai in attrs}

        hid = self._generate_hid(exp)
        doc.update(**{'starttime': exp.starttime,
                      'timestamp': now,
                      'hash_id': hid})

        db.experiments.insert(doc)
        # exp.hash_id = hid

    def update_experiment(self, exp, err_msg):
        db = self.db
        hid = self._generate_hid(exp)
        doc = db.experiments.find_one({'hash_id': hid})
        if doc:
            db.experiments.update({'_id': doc['_id']},
                                  {'$set': {'status': err_msg or 'Finished',
                                            'timestamp': datetime.now()}})

    def _generate_hid(self, exp):
        md5 = hashlib.md5()
        md5.update(exp.name)
        md5.update(exp.spectrometer)
        md5.update(exp.starttime.isoformat())
        return md5.hexdigest()

    def add_run(self, run, exp):
        db = self.db
        # attrs = ('record_id', 'timestamp', 'experiment_name', 'state')
        # doc = {k: getattr(run, k) for k in attrs}
        doc = self._make_run_doc(run, exp)
        db.runs.insert(doc)

    def add_device_post(self, devs):

        clt = self._client
        db = clt[self.database_name]
        now = datetime.now()
        doc = {'timestamp': now,
               'timestampt': now.strftime('%H:%M:%S'),
               'timestampf': time.mktime(now.timetuple())}

        values = []
        for di in devs:
            for vk, cv, ui in zip(di.value_keys, di.current_values, di.units):
                values.append({'device': di.name,
                               'name': vk,
                               'value': cv,
                               'units': ui})

        doc['values'] = values

        pprint(doc, width=4)
        db.devices.insert(doc)

    # private
    def _make_run_doc(self, run, exp):
        spec = run.spec

        d = {k: getattr(spec, k) for k in ('runid',
                                           'analysis_type',
                                           'sample',
                                           'extract_value',
                                           'duration',
                                           'cleanup',
                                           'position',
                                           'comment',
                                           'material',
                                           'project',
                                           'mass_spectrometer',
                                           'extract_device',
                                           'state')}

        d['experiment_name'] = exp.name
        if spec.analysis_timestamp:
            d['date'] = spec.analysis_timestamp.strftime('%m/%d/%Y %I:%M:%S %p')
            d['timestamp'] = time.mktime(spec.analysis_timestamp.timetuple())
            d['runtime'] = spec.analysis_timestamp.strftime('%I:%M:%S %p')
        else:
            d['date'] = ''
            d['timestamp'] = ''
            d['runtime'] = ''

        for si in SCRIPT_NAMES:
            d[si] = getattr(spec, si)

        return d


if __name__ == '__main__':
    from random import random, choice, randint

    # c = LabspyClient(bind=False, host='129.138.12.138', port=27017)
    c = LabspyClient(bind=False, host='localhost', port=3001)

    class Dev():
        def __init__(self, name, values, units):
            self.name = name
            self.units = units
            self.value_keys = values
            self.current_values = [random() for k in values]


    a = Dev('pneumatic', ('pressure',), ('torr',))
    b = Dev('environment',
            ('temperature', 'humidity'), ('C', '%'))

    # c.add_device_post([a, b])

    class Exp():
        def __init__(self, name, user, spec, status):
            self.name = name
            self.user = user
            self.spectrometer = spec
            self.status = status
            self.starttime = datetime(2014, 11, 1, 12, 10, 10)

    class Spec():
        def __init__(self, record_id):
            self.runid = record_id
            self.mass_spectrometer='jan'
            self.extract_device='LF'
            self.analysis_timestamp = datetime.now()
            self.state = choice(['Finished', 'Canceled', 'Failed'])
            self.analysis_type = "unknown"
            self.sample = "FC-2"
            self.extract_value = random()*2
            self.duration = randint(100,200)
            self.cleanup = randint(100,200)
            self.position = 1
            self.comment = "Test comment"
            self.material = "sanidine"
            self.project = "Monitor"
            self.measurement_script = 'm'
            self.extraction_script = 'e'
            self.post_measurement_script = 'pm'
            self.post_equilibration_script = 'pq'

    class Run():
        def __init__(self, *args, **kw):
            self.spec = Spec(*args, **kw)


    e = Exp('Current Experiment', 'foobar', 'Jan', 'Running')
    # c.add_experiment(e)
    # print e.hash_id
    # hid='076441e14fe0e09086626f25f216ca04'
    # e.hash_id=hid
    # c.update_experiment(e)

    for i in range(6):
        c.add_run(Run('12346-{:02n}'.format(i + 1)), e)

# ============= EOF =============================================



