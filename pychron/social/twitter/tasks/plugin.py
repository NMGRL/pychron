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
from __future__ import absolute_import
from traits.api import List, Instance

from pychron.envisage.tasks.base_task_plugin import BaseTaskPlugin
from pychron.experiment.events import ExperimentEventAddition, START_QUEUE, END_QUEUE, START_RUN, END_RUN
from pychron.social.twitter.client import TwitterClient

from pychron.social.twitter.tasks.preferences import TwitterPreferencesPane, TwitterExperimentPreferencesPane


class TwitterPlugin(BaseTaskPlugin):
    id = 'pychron.social.twitter.plugin'
    name = 'Twitter'

    events = List(contributes_to='pychron.experiment.events')
    client = Instance(TwitterClient)

    def _service_offers_default(self):
        """
        """
        so = self.service_offer_factory(protocol='pychron.social.twitter.client.TwitterClient',
                                        factory=TwitterClient)
        return [so]

    def test_api(self):
        s = self.client
        return s.test_api()

    def _end_run_event(self, ctx):
        self.debug('end run event')
        enabled = self.application.get_boolean_preference('pychron.twitter.experiment.enabled')
        if enabled:
            run = ctx['run']
            self.client.twit('End Run {}'.format(run.runid))

    def _end_experiment_event(self, ctx):
        self.debug('end experiment event')
        # d = {'end': 'now',
        #      'summary': 'Experiment: {} {}'.format(ctx['experiment_name'],
        #                                            ctx['err_message'])}
        #
        enabled = self.application.get_boolean_preference('pychron.twitter.experiment.enabled')
        if enabled:
            self.client.twit('End Experiment {}'.format(ctx['experiment_name']))

    def _start_experiment_event(self, ctx):
        self.debug('start experiment event')

        enabled = self.application.get_boolean_preference('pychron.twitter.experiment.enabled')
        if enabled:
            self.client.twit('Start Experiment {}'.format(ctx['experiment_name']))

    def _client_default(self):
        return TwitterClient()

    def _events_default(self):
        e1 = ExperimentEventAddition(id='pychron.twitter.start_experiment_event',
                                     level=START_QUEUE,
                                     action=self._start_experiment_event)
        e2 = ExperimentEventAddition(id='pychron.twitter.end_experiment_event',
                                     level=END_QUEUE,
                                     action=self._end_experiment_event)

        e3 = ExperimentEventAddition(id='pychron.twitter.end_run_event',
                                     level=END_RUN,
                                     action=self._end_run_event)
        return [e1, e2, e3]

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
        return [TwitterPreferencesPane, TwitterExperimentPreferencesPane]

# ============= EOF =============================================
