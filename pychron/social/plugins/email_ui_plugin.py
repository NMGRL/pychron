#===============================================================================
# Copyright 2011 Jake Ross
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#===============================================================================



#=============enthought library imports=======================
#============= standard library imports ========================
#============= local library imports  ==========================
from apptools.preferences.preference_binding import bind_preference
from pychron.social.email_manager import EmailManager
from pychron.envisage.core.core_ui_plugin import CoreUIPlugin

class EmailUIPlugin(CoreUIPlugin):
    def _preferences_pages_default(self):
        from email_preferences_page import EmailPreferencesPage
        return [EmailPreferencesPage]

    def _views_default(self):
        return [self._create_user_view]

    def _create_user_view(self, *args, **kw):
        args = dict(id='social.email.users',
                    name='Users',
                    category='Social',
                    obj=self.application.get_service(EmailManager)
                  )
        return self.traitsuiview_factory(args, kw)
    def start(self):
        em = self.application.get_service(EmailManager)
        bind_preference(em, 'outgoing_server', 'pychron.email.smtp_host')
        bind_preference(em, 'server_username', 'pychron.email.username')
        bind_preference(em, 'server_password', 'pychron.email.password')

    def stop(self):
        em = self.application.get_service(EmailManager)
        em.save_users()


        # em.broadcast('fadsfasdfasdf')
#============= EOF =====================================
