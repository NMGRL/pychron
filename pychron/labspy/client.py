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

import hashlib
import os
import time
from datetime import datetime
from threading import Thread, Lock

# ============= enthought library imports =======================
from apptools.preferences.preference_binding import bind_preference
from traits.api import Instance, Bool, Int

from pychron.core.helpers.logger_setup import logging_setup
from pychron.core.yaml import yload
from pychron.hardware.core.i_core_device import ICoreDevice
from pychron.labspy.database_adapter import LabspyDatabaseAdapter
from pychron.loggable import Loggable
from pychron.paths import paths
from pychron.pychron_constants import SCRIPT_NAMES, NULL_STR


def auto_connect(func):
    def wrapper(obj, *args, **kw):
        with obj.session_lock:
            if not obj.db.connected:
                obj.connect()

            if obj.db.connected:
                with obj.db.session_ctx(use_parent_session=False):
                    return func(obj, *args, **kw)

    return wrapper


def auto_reset_connect(func):
    def wrapper(obj, *args, **kw):
        with obj.session_lock:
            if not obj.db.connected:
                obj.connect()
            else:
                obj.db.reset_connection()
                obj.db.reset_connection()
                obj.db.connect()

            if obj.db.connected:
                with obj.db.session_ctx(use_parent_session=False):
                    return func(obj, *args, **kw)

    return wrapper


class NotificationTrigger(object):
    def __init__(self, params):
        self._params = params

    def test(self, dev, tag, val, unit):
        mdev = self._params["device"]
        mtag = self._params["tag"]
        mcmp = self._params["cmp"]
        munit = self._params["units"]

        if dev == mdev and mtag == tag and munit == unit:
            return eval(mcmp, {"x": val})

    def notify(self, val, unit):
        addrs = self._params["addresses"]
        dev = self._params["device"]
        tag = self._params["tag"]
        mcmp = self._params["cmp"]

        sub = self._params["subject"]
        message = """device: {}
tag: {}
cmp: {}
test_value: {} ({})""".format(
            dev, tag, mcmp, val, unit
        )
        return addrs, sub, message


class LabspyClient(Loggable):
    """
    Used to add experiments and runs to the database.
    Used in conjunction with ExperimentPlugin
    """

    db = Instance(LabspyDatabaseAdapter)

    use_connection_status = Bool
    connection_status_period = Int

    _timer = None
    session_lock = None

    def __init__(self, bind=True, *args, **kw):
        super(LabspyClient, self).__init__(*args, **kw)
        if bind:
            self.bind_preferences()
            # self.start()
        self.session_lock = Lock()

    def bind_preferences(self):
        self.db.bind_preferences()
        bind_preference(
            self, "use_connection_status", "pychron.labspy.use_connection_status"
        )
        bind_preference(
            self, "connection_status_period", "pychron.labspy.connection_status_period"
        )

    def test_connection(self, **kw):
        return self.db.connect(**kw)

    def start(self):
        self.debug("Start Connection status timer")
        if self.application and self.use_connection_status:
            self.debug("timer started period={}".format(self.connection_status_period))

            devs = self.application.get_services(ICoreDevice)
            if devs:
                t = Thread(target=self._connection_status, name="ConnectionStatus")
                t.setDaemon(True)
                t.start()

            else:
                self.debug("No devices to check for connection status")

    def get_latest_lab_temperatures(self):
        return self.db.get_latest_lab_temperatures()

    def get_latest_lab_humiditys(self):
        return self.db.get_latest_lab_humiditys()

    def get_latest_lab_pneumatics(self):
        return self.db.get_latest_lab_pneumatics()

    def _connection_status(self, verbose=False):
        # if verbose:
        #     self.debug('Connection Status. ndevs={}'.format(len(devs or ())))
        # if devs:

        devs = self.application.get_services(ICoreDevice)

        period = self.connection_status_period
        while 1:
            st = time.time()
            ts = datetime.now()
            for dev in devs:
                # remove Communicator for name. e.g SerialCommunicator to Serial
                cname = dev.communicator.__class__.__name__
                com_name = cname[:-12]
                try:
                    self.update_connection(
                        ts,
                        dev.name,
                        com_name,
                        dev.communicator.address,
                        dev.test_connection(),
                        verbose=verbose,
                    )
                except BaseException as e:
                    self.debug(
                        "Connection status. update connection failed: "
                        "error={}".format(e)
                    )
                    break

            et = time.time() - st
            time.sleep(max(0, period - et))

    @auto_reset_connect
    def add_experiment(self, exp):
        name = exp.name
        starttime = exp.start_timestamp
        mass_spectrometer = exp.mass_spectrometer
        username = exp.username
        hid = self._generate_hid(
            name, starttime.isoformat(), mass_spectrometer, username
        )
        self.db.add_experiment(
            hashid=hid,
            name=name,
            system=mass_spectrometer,
            user=username,
            start_time=starttime,
        )

    @auto_connect
    def update_experiment(self, exp, err_msg):
        # if self.db.connected:
        # with self.db.session_ctx():
        #         hid = self._generate_hid(exp)
        #         exp = self.db.get_experiment(hid)
        #         # exp.EndTime = exp.endtime
        #         # exp.State = err_msg
        hid = self._generate_hid_from_exp(exp)
        exp = self.db.get_experiment(hid)

    @auto_connect
    def update_connection(self, ts, devname, com, addr, status, verbose=False):
        if verbose:
            self.debug(
                "Setting connection status for dev={},com={},addr={},status={}".format(
                    devname, com, addr, status
                )
            )
        appname = self.application.name

        user = NULL_STR
        try:
            appname, user = appname.split("-")
        except ValueError:
            pass

        self.db.set_connection(
            ts, appname.strip(), user.strip(), devname, com, addr, status
        )

    @auto_connect
    def update_status(self, **kw):
        self.debug("update status not enabled")
        return

        status = self.db.get_status()
        if not status:
            status = self.db.add_status()

        for k, v in kw.items():
            setattr(status, k, v)

    @auto_reset_connect
    def add_run(self, run, exp):
        hid = self._generate_hid_from_exp(exp)
        expid = self.db.get_experiment(hid)
        if not expid:
            self.add_experiment(exp)
            expid = self.db.get_experiment(hid)

        if not expid:
            # use a dumpy experiment id just so that the analysis is saved
            expid = "1"

        self.db.add_analysis(expid, self._run_dict(run))
        ms = run.spec.mass_spectrometer.capitalize()

        config = self._get_configuration()

        for name, units, attr, atypes in config:
            units = units or ""
            if atypes[0] == "all":
                add = True
            else:
                add = run.analysis_type in atypes

            if add:
                args = []
                if attr == "peak_center":
                    attr = "get_reference_peakcenter_result"
                elif "/" in attr:
                    args = (attr,)
                    attr = "get_ratio"

                try:
                    v = getattr(run, attr)(*args)
                except AttributeError:
                    continue

                self.db.add_measurement(
                    "{}Monitor".format(ms), "{}{}".format(ms, name), v, units
                )

    @auto_connect
    def add_measurement(self, dev, tag, val, unit):
        val = float(val)
        self.debug(
            "adding measurement dev={} process={} value={} ({})".format(
                dev, tag, val, unit
            )
        )
        try:
            self.db.add_measurement(dev, tag, val, unit)
            self._check_notifications(dev, tag, val, unit)
        except BaseException as e:
            self.debug("failed adding measurement. {}".format(e))

    def connect(self):
        self.warning("not connected to db {}".format(self.db.public_url))
        return self.db.connect()

    @property
    def notification_triggers(self):
        p = paths.notification_triggers
        return [NotificationTrigger(i) for i in yload(p)]

    # private
    def _get_configuration(self):
        """
        eg;
         config = [('PeakCenter', 'DAC (V)', 'peak_center', ('all',)),
                   ('Ar40/Ar36', '', 'Ar40/Ar36', ('air',))]

        -
         - PeakCenter
         - DAC (V)
         -
          - all
        -
         - Ar40/Ar36
         -
         -
          - air

        :return:
        """
        config = []
        p = paths.labspy_client_config
        if p and os.path.isfile(p):
            config = yload(p)

        return config

    def _check_notifications(self, dev, tag, val, unit):
        if not os.path.isfile(paths.notification_triggers):
            self.debug(
                "no notification trigger file available. {}".format(
                    paths.notification_triggers
                )
            )
            return

        ns = []
        for nt in self.notification_triggers:
            self.debug("testing {} {} {} {}".format(dev, tag, val, unit))
            if nt.test(dev, tag, val, unit):
                self.debug("notification triggered")
                ns.append(nt.notify(val, unit))
        self.debug("notifications: {}".format(ns))
        if ns:
            emailer = self.application.get_service(
                "pychron.social.email.emailer.Emailer"
            )
            if emailer:
                for addrs, sub, message in ns:
                    emailer.send(addrs, sub, message)
            else:
                self.warning("Email Plugin not enabled")

    def _db_default(self):
        return LabspyDatabaseAdapter()

    def _run_dict(self, run):
        spec = run.spec
        return {
            "identifier": spec.identifier,
            "aliquot": spec.aliquot,
            "increment": spec.increment,
        }

        d = {
            dbk: getattr(spec, k)
            for k, dbk in (
                ("runid", "Runid"),
                ("analysis_type", "analysis_type"),
                ("analysis_timestamp", "TimeStamp"),
                ("sample", "Sample"),
                ("extract_value", "ExtractValue"),
                ("extract_units", "ExtractUnits"),
                ("duration", "Duration"),
                ("cleanup", "Cleanup"),
                ("position", "Position"),
                ("comment", "Comment"),
                ("material", "Material"),
                ("project", "Project"),
                ("state", "State"),
            )
        }

        for si in SCRIPT_NAMES:
            k = "".join([sii.capitalize() for sii in si.split("_")[:-1]])
            d[k] = getattr(spec, si)

        return d

    def _generate_hid_from_exp(self, exp):
        return self._generate_hid(
            exp.name,
            exp.start_timestamp.isoformat(),
            exp.mass_spectrometer,
            exp.username,
        )

    def _generate_hid(self, name, starttime, mass_spectrometer, username):
        md5 = hashlib.md5()
        md5.update(name.encode("utf8"))
        md5.update(starttime.encode("utf8"))
        md5.update(mass_spectrometer.encode("utf8"))
        md5.update(username.encode("utf8"))
        return md5.hexdigest()


# ================= testing =========================
def main1():
    from random import random

    # from pychron.paths import paths

    paths.build("_dev")

    # def add_runs(c, e):
    # class Spec():
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
    #     c.update_status(Message='This is a long message',
    #                     ShortMessage='This is a short message')

    def add_measurements(c):
        for i in range(100):
            c.add_measurement("AirPressure", "pneumatics", random(), "PSI")
            c.add_measurement("Environmental", "temperature", random() * 2 + 70, "C")
            c.add_measurement("Environmental", "humidity", random() * 5 + 50, "%")

            time.sleep(1)

    logging_setup("labspyclient", use_archiver=False)
    # c = LabspyClient(bind=False, host='129.138.12.138', port=27017)
    # c = MeteorLabspyClient(bind=False, host='localhost', port=3001)
    # # update_state(c)
    # for i in range(10):
    # add_device(c)
    # time.sleep(1)

    clt = LabspyClient(bind=False)
    clt.db.host = "localhost"
    clt.db.username = os.environ.get("DB_USER")
    clt.db.password = os.environ.get("DB_PWD")
    clt.db.name = "labspy"
    clt.test_connection()

    # set status
    # update_status(clt)

    # measurements
    add_measurements(clt)

    # experiments/runs
    # exp = add_experiment(clt)
    # add_runs(clt, exp)


def main2():
    clt = LabspyClient(bind=False)
    clt.db.host = "129.138.12.160"
    clt.db.username = os.environ.get("DB_USER")
    clt.db.password = os.environ.get("DB_PWD")
    clt.db.name = "labspy"
    clt.test_connection()

    for tag in ("lab_temperatures", "lab_humiditys", "lab_pneumatics"):
        st = time.time()
        try:
            print(getattr(clt, "get_latest_{}".format(tag))())
            print("Get latest {}. elapsed: {}".format(tag, time.time() - st))
        except BaseException as e:
            pass


if __name__ == "__main__":
    main2()
# ============= EOF =============================================
