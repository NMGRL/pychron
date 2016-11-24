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
from traits.api import List, Instance

from pychron.envisage.tasks.base_task_plugin import BaseTaskPlugin
from pychron.experiment.events import ExperimentEventAddition
from pychron.social.google_calendar.client import GoogleCalendarClient
from pychron.social.google_calendar.tasks.preferences import GoogleCalendarPreferencesPane, \
    GoogleCalendarExperimentPreferencesPane


class GoogleCalendarPlugin(BaseTaskPlugin):
    id = 'pychron.google_calendar.plugin'
    name = 'GoogleCalendar'

    events = List(contributes_to='pychron.experiment.events')
    client = Instance(GoogleCalendarClient)

    def _service_offers_default(self):
        """
        """
        so = self.service_offer_factory(protocol='pychron.social.google_calendar.client.GoogleCalendarClient',
                                        factory=GoogleCalendarClient)
        return [so]

    def test_api(self):
        s = self.client
        return s.test_api()

    def _end_experiment_event(self, ctx):
        self.debug('end experiment event')
        client = self.client
        d = {'end': 'now',
             'summary': 'Experiment: {} {}'.format(ctx['experiment_name'],
                                                   ctx['err_message'])}
        client.edit_event(d)

    def _start_experiment_event(self, ctx):
        self.debug('start experiment event')
        client = GoogleCalendarClient()

        run_delay = self.application.preferences.get('pychron.google_calendar.experiment.run_delay')
        enabled = self.application.get_boolean_preference('pychron.google_calendar.experiment.enabled')
        if enabled:
            self.debug('calendar enabled')
            nfinished = ctx['nruns_finished']
            if nfinished >= run_delay:
                summary = 'Experiment: {}'.format(ctx['experiment_name'])
                description = ''
                client.post_event(summary,
                                  description,
                                  ctx['etf_iso'])

    def _client_default(self):
        return GoogleCalendarClient()

    def _events_default(self):
        e1 = ExperimentEventAddition(id='pychron.google_calendar.start_event',
                                     action=self._start_experiment_event)
        e2 = ExperimentEventAddition(id='pychron.google_calendar.end_event',
                                     action=self._end_experiment_event)
        return [e1, e2]

    # def _preferences_default(self):
    #     return ['file://{}'.format('')]
    #
    # def _task_extensions_default(self):
    #
    #     return [TaskExtension(SchemaAddition)]
    # def _tasks_default(self):
    #     return [TaskFactory(factory=self._task_factory,
    #                         protocol=FurnaceTask)]

    def _preferences_panes_default(self):
        return [GoogleCalendarPreferencesPane, GoogleCalendarExperimentPreferencesPane]

# ============= EOF =============================================
