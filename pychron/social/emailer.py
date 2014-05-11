#===============================================================================
# Copyright 2013 Jake Ross
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

#============= enthought library imports =======================
from apptools.preferences.preference_binding import bind_preference
from traits.api import HasTraits, Str, List, Enum, Bool
from traitsui.api import View
#============= standard library imports ========================
import os
import smtplib
#============= local library imports  ==========================
from pychron.config_loadable import ConfigMixin
from pychron.paths import paths


class User(HasTraits):
    name = Str
    email = Str
    enabled = Bool
    level = Enum(0, 1, 2)

    telephone = Str

    def edit_view(self):
        return View('name',
                    'email',
                    'level',
                    'telephone')


class Emailer(ConfigMixin):
    server_username = Str
    server_password = Str
    users = List

    def __init__(self, *args, **kw):
        super(Emailer, self).__init__(*args, **kw)
        bind_preference(self, 'server_username', 'pychron.email')
        bind_preference(self, 'server_password', 'pychron.email')

    def connect(self):
        if self._server is None:
            try:
                server = smtplib.SMTP(self.outgoing_server, self.port)
                server.ehlo()
                server.starttls()
                server.ehlo()

                server.login(self.server_username, self.server_password)
                self._server = server
            except smtplib.SMTPServerDisconnected:
                self.warning('SMTPServer not properly configured')

        return self._server

    def broadcast(self, text, level=0, subject=None):

        recipients = self.get_emails(level)
        self.debug('broadcasting to recipients {}. level={}'.format(recipients, level))
        if recipients:
            r = ','.join(recipients)

            msg = self._message_factory(text, r, subject)
            server = self.connect()
            if server:
                self.info('Broadcasting message to {}'.format(r))
                server.sendmail(self.sender, recipients, msg.as_string())
                server.close()
            else:
                self.debug('SMTP server not available')

    def get_emails(self, level):
        return [u.email for u in self.users
                if u.email_enabled and u.level <= level]

    def _message_factory(self, text, recipients, subject='!Pychron Alert!'):
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText

        msg = MIMEMultipart()
        msg['From'] = self.sender  # 'nmgrl@gmail.com'
        msg['To'] = recipients
        msg['Subject'] = subject

        msg.attach(MIMEText(text))
        return msg

    def _users_default(self):
        path = os.path.join(paths.setup_dir, 'users.cfg')
        config = self.configparser_factory()
        config.read(path)
        users = []
        for user in config.sections():
            self.info('loading user {}'.format(user))
            kw = dict(name=user)
            for opt, func in [('email', None), ('level', 'int'), ('enabled', 'boolean')]:
                if func is None:
                    func = config.get
                else:
                    func = getattr(config, 'get{}'.format(func))

                kw[opt] = func(user, opt)
            users.append(User(**kw))

        return users

        #============= EOF =============================================
