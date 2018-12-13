# ===============================================================================
# Copyright 2013 Jake Ross
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
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.envisage.tasks.base_task_plugin import BaseTaskPlugin
from pychron.experiment.events import ExperimentEventAddition, START_QUEUE, END_QUEUE
from pychron.social.email.emailer import Emailer
from pychron.social.email.experiment_notifier import ExperimentNotifier
from pychron.social.email.tasks.preferences import EmailPreferencesPane


class EmailPlugin(BaseTaskPlugin):
    id = 'pychron.social.email.plugin'
    name = 'Email'
    test_email_server_description = 'Test connection to the SMTP Email Server'
    events = List(contributes_to='pychron.experiment.events')
    experiment_notifier = Instance(ExperimentNotifier)

    def test_email_server(self):
        e = self._email_factory()
        return e.test_email_server()

    # private
    # def _start_queue(self, ctx):
    #     if ctx.get('use_email'):
    #         subject = 'Experiment "{}" Started'.format(ctx.get('name'))
    #         self.info('Notifying user={} email={}'.format(ctx.get('username'), ctx.get('email')))
    #         self.experiment_notifier.notify(ctx, subject)
    #
    # def _end_queue(self, ctx):
    #     if ctx.get('use_email'):
    #         tag = 'Stopped' if ctx.get('err_message') else 'Finished'
    #         subject = 'Experiment "{}" {}'.format(ctx.get('name'), tag)
    #         self.info('Notifying user={} email={}'.format(ctx.get('username'), ctx.get('email')))
    #         self.experiment_notifier.notify(ctx, subject)

    def _email_factory(self):
        return Emailer()

    def _preferences_panes_default(self):
        return [EmailPreferencesPane]

    def _service_offers_default(self):
        so = self.service_offer_factory(factory=self._email_factory,
                                        protocol='pychron.social.email.emailer.Emailer')
        return [so]

    def _experiment_notifier_default(self):
        exp = ExperimentNotifier(emailer=Emailer())
        return exp

    def _events_default(self):
        evts = [ExperimentEventAddition(id='pychron.experiment_notifier.start_queue',
                                        action=self.experiment_notifier.start_queue,
                                        level=START_QUEUE),
                ExperimentEventAddition(id='pychron.experiment_notifier.end_queue',
                                        action=self.experiment_notifier.end_queue,
                                        level=END_QUEUE)]
        return evts

 # ============= EOF =============================================
