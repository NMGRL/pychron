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
from traits.api import on_trait_change, List

from pychron.envisage.tasks.base_task_plugin import BaseTaskPlugin
from pychron.experiment.events import ExperimentEventAddition
from pychron.labspy.client import LabspyClient
from pychron.labspy.tasks.preferences import LabspyPreferencesPane, LabspyExperimentPreferencesPane


class LabspyClientPlugin(BaseTaskPlugin):
    name = 'LabspyClient'
    id = 'pychron.labspy_client.plugin'

    events = List(contributes_to='pychron.experiment.events')

    def _events_default(self):
        e1 = ExperimentEventAddition(id='pychron.labspy.add_run',
                                     action=self._add_run)
        e2 = ExperimentEventAddition(id='pychron.labspy.add_experiment',
                                     action=self._add_experiment)
        return [e1, e2]

    def _add_run(self, ctx):
        self.debug('add run')
        if self.application.get_boolean_preference('pychron.labspy.experiment.enabled'):
            client = self.application.get_service(LabspyClient)
            client.add_run(ctx['run'], ctx['experiment_queue'])

    def _add_experiment(self, ctx):
        self.debug('add experiment')
        if self.application.get_boolean_preference('pychron.labspy.experiment.enabled'):
            client = self.application.get_service(LabspyClient)
            client.add_experiment(ctx['experiment_name'],
                                  ctx['starttime'],
                                  ctx['mass_spectrometer'],
                                  ctx['username'])

    def _labspy_client_factory(self, *args, **kw):
        return LabspyClient(application=self.application)

    def _service_offers_default(self):
        so = self.service_offer_factory(protocol=LabspyClient,
                                        factory=self._labspy_client_factory)
        return [so]

    def _preferences_panes_default(self):
        return [LabspyPreferencesPane, LabspyExperimentPreferencesPane]

    def test_communication(self):
        lc = self.application.get_service(LabspyClient)
        return lc.test_connection(warn=False)

    @on_trait_change('application:started')
    def _start(self):
        plugin = self.application.get_plugin('pychron.dashboard.tasks.server.plugin.DashboardServerPlugin')
        if not plugin:
            client = self.application.get_service(LabspyClient)
            client.start()

# ============= EOF =============================================
