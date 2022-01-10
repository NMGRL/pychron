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

    def run_start(self, ctx):
        self.debug("run start")
        url = self._make_url("run_start")

        exp_id = make_exp_key(ctx)
        expire = self._make_expire(ctx["current_run_duration"])
        resp = requests.post(url, json={"key": exp_id, "expire": expire})
        self.debug("run start resp={}".format(resp.json()))

    def run_end(self, ctx):
        self.debug("run end")
        url = self._make_url("run_end")

        exp_id = make_exp_key(ctx)
        expire = self._make_expire(ctx["delay_after_run"])
        resp = requests.post(url, json={"key": exp_id, "expire": expire})
        self.debug("run end resp={}".format(resp.json()))

    def experiment_start(self, ctx):
        self.debug("experiment start")
        url = self._make_url("experiment_start")

        exp_id = make_exp_key(ctx)
        expire = self._make_expire(60)
        resp = requests.post(url, json={"key": exp_id, "expire": expire})
        self.debug("experiment start resp={}".format(resp.json()))

    def experiment_end(self, ctx):
        self.debug("experiment end")
        url = self._make_url("experiment_end")

        exp_id = make_exp_key(ctx)
        resp = requests.post(url, json={"key": exp_id})
        self.debug("experiment end resp={}".format(resp.json()))

    def _make_expire(self, value):
        return max(60, float(value)) * self.pad

    def _make_url(self, tag):
        return "http://{}:{}/{}".format(self.host, self.port, tag)


class WatchDogPlugin(BaseTaskPlugin):
    id = "pychron.watchdog.plugin"
    events = List(contributes_to="pychron.experiment.events")
    worker = Instance(WatchDogWorker, ())

    def _events_default(self):
        e1 = ExperimentEventAddition(
            id="pychron.watchdog.experiment_start",
            action=self.worker.experiment_start,
            level=START_QUEUE,
        )
        e2 = ExperimentEventAddition(
            id="pychron.watchdog.experiment_end",
            level=END_QUEUE,
            action=self.worker.experiment_end,
        )
        e3 = ExperimentEventAddition(
            id="pychron.watchdog.run_start",
            level=START_RUN,
            action=self.worker.run_start,
        )
        e4 = ExperimentEventAddition(
            id="pychron.watchdog.run_end",
            level=END_RUN,
            action=self.worker.run_end,
        )
        return [e1, e2, e3, e4]

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
