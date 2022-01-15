# ===============================================================================
# Copyright 2019 Jake Ross
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
from traits.api import List, Int, HasTraits, Str, Bool, Float, Instance

# ============= standard library imports ========================
import datetime
import time
import requests

# ============= local library imports  ==========================
from pychron.core.ui.preference_binding import bind_preference
from pychron.envisage.tasks.base_task_plugin import BaseTaskPlugin
from pychron.experiment.events import (
    ExperimentEventAddition,
    START_QUEUE,
    END_QUEUE,
    START_RUN,
    END_RUN,
    SAVE_RUN,
)
from pychron.watchdog.tasks.preferences import WatchDogPreferencesPane
from pychron.loggable import Loggable


def make_exp_key(ctx):
    return "{}.{}".format(ctx["mass_spectrometer"], ctx["experiment_name"])


class WatchDogWorker(Loggable):
    host = Str
    port = Int(5001)
    pad = Float(1.25)

    def __init__(self, *args, **kw):
        super(WatchDogWorker, self).__init__(*args, **kw)
        self._bind_preferences()

    def _bind_preferences(self):
        prefid = "pychron.watchdog"
        bind_preference(self, "host", "{}.host".format(prefid))
        bind_preference(self, "port", "{}.port".format(prefid))
        bind_preference(self, "pad", "{}.pad".format(prefid))

    def test_api(self):
        ret, err = True, ""
        try:
            self._get("status")
        except BaseException as e:
            ret = False
            err = str(e)

        return ret, err

    def start_run_handler(self, ctx):
        self.debug("run start")
        url = self._make_url("run_start")

        exp_id = make_exp_key(ctx)
        expire = self._make_expire(ctx["current_run_duration"])
        resp = requests.post(url, json={"key": exp_id, "expire": expire})
        self.debug("run start resp={}".format(resp.json()))

    def end_run_handler(self, ctx):
        self.debug("run end")
        url = self._make_url("run_end")

        exp_id = make_exp_key(ctx)
        expire = self._make_expire(ctx["delay_after_run"])
        resp = requests.post(url, json={"key": exp_id, "expire": expire})
        self.debug("run end resp={}".format(resp.json()))

    def save_run_handler(self, ctx):
        self.debug("save run")
        url = self._make_url("run_save")
        exp_id = make_exp_key(ctx)
        expire = self._make_expire(180)
        resp = requests.post(url, json={"key": exp_id, "expire": expire})
        self.debug("run end resp={}".format(resp.json()))

    def start_experiment_handler(self, ctx):
        self.debug("experiment start")
        url = self._make_url("experiment_start")

        exp_id = make_exp_key(ctx)
        expire = self._make_expire(60)
        addresses = ctx["group_emails"][1]

        resp = requests.post(
            url, json={"key": exp_id, "expire": expire, "addresses": addresses}
        )
        self.debug("experiment start resp={}".format(resp.json()))

    def end_experiment_handler(self, ctx):
        self.debug("experiment end")
        url = self._make_url("experiment_end")

        exp_id = make_exp_key(ctx)
        resp = requests.post(url, json={"key": exp_id})
        self.debug("experiment end resp={}".format(resp.json()))

    def _get(self, tag, **kw):
        url = self._make_url(tag)
        resp = requests.get(url)
        return resp.json()

    def _make_expire(self, value):
        return max(120, float(value)) * self.pad

    def _make_url(self, tag):
        return "http://{}:{}/{}".format(self.host, self.port, tag)


class WatchDogPlugin(BaseTaskPlugin):
    id = "pychron.watchdog.plugin"
    events = List(contributes_to="pychron.experiment.events")
    worker = Instance(WatchDogWorker, ())

    def test_api(self):
        return self.worker.test_api()

    def _events_default(self):
        e1 = ExperimentEventAddition(
            id="pychron.watchdog.experiment_start",
            action=self.worker.start_experiment_handler,
            level=START_QUEUE,
        )
        e2 = ExperimentEventAddition(
            id="pychron.watchdog.experiment_end",
            level=END_QUEUE,
            action=self.worker.end_experiment_handler,
        )
        e3 = ExperimentEventAddition(
            id="pychron.watchdog.run_start",
            level=START_RUN,
            action=self.worker.start_run_handler,
        )
        e4 = ExperimentEventAddition(
            id="pychron.watchdog.run_end",
            level=END_RUN,
            action=self.worker.end_run_handler,
        )
        e5 = ExperimentEventAddition(
            id="pychron.watchdog.run_save",
            level=SAVE_RUN,
            action=self.worker.save_run_handler,
        )
        return [e1, e2, e3, e4, e5]

    # def _service_offers_default(self):
    #     """
    #     """
    #     # so = self.service_offer_factory()
    #     return []

    # def _preferences_default(self):
    #     return ['file://']
    #
    # def _task_extensions_default(self):
    #
    #     return [TaskExtension(SchemaAddition)]
    # def _tasks_default(self):
    #     return [TaskFactory(factory=self._task_factory,
    #                         protocol=FurnaceTask)]

    def _preferences_panes_default(self):
        return [WatchDogPreferencesPane]


# ============= EOF =============================================
