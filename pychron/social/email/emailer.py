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

import os
# ============= standard library imports ========================
import smtplib
import time
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from apptools.preferences.preference_binding import bind_preference
from traits.api import HasTraits, Str, Enum, Bool, Int
from traitsui.api import View

# ============= local library imports  ==========================
from pychron.loggable import Loggable


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


class Emailer(Loggable):
    server_username = Str
    server_password = Str
    server_host = Str
    server_port = Int

    sender = Str('pychron@gmail.com')

    def __init__(self, *args, **kw):
        super(Emailer, self).__init__(*args, **kw)

        self._server = None

        bind_preference(self, 'server_username', 'pychron.email.server_username')
        bind_preference(self, 'server_password', 'pychron.email.server_password')
        bind_preference(self, 'server_host', 'pychron.email.server_host')
        bind_preference(self, 'server_port', 'pychron.email.server_port')
        if not self.server_port:
            self.server_port = 587

    def test_email_server(self):
        return bool(self.connect(warn=False, test=True))

    def connect(self, warn=True, test=False):
        try:
            server = smtplib.SMTP(self.server_host, self.server_port, timeout=5)
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(self.server_username, self.server_password)
            if test:
                server.quit()
                return True
        except (smtplib.SMTPServerDisconnected, BaseException) as e:
            self.debug('SMTPServer connection err: {}'
                       'host={}, user={}, port={}'.format(e, self.server_host, self.server_username, self.server_port))
            if warn:
                self.warning('SMTPServer not properly configured')
            server = None

        return server

    def send(self, addrs, sub, msg, paths=None):
        self.info('Send email. addrs: {}'.format(addrs, sub))
        # self.debug('========= Message ========')
        # for m in msg.split('\n'):
        #     self.debug(m)
        # self.debug('==========================')

        for i in range(10):
            server = self.connect()
            if server is not None:
                break
            self.debug('doing email connection retry {}'.format(i))
            time.sleep(1)

        if server:
            if not isinstance(addrs, (list, tuple)):
                addrs = [addrs]

            msg = self._message_factory(addrs, sub, msg, paths)
            try:
                server.sendmail(self.sender, addrs, msg.as_string())
                server.quit()
                return True
            except BaseException as e:
                self.warning('Failed sending mail. {}'.format(e))
        else:
            self.warning('Failed connecting to server')

    def _message_factory(self, addrs, sub, txt, paths):
        msg = MIMEMultipart()
        msg['From'] = self.sender  # 'nmgrl@gmail.com'
        msg['To'] = ','.join(addrs)
        msg['Subject'] = sub
        msg.attach(MIMEText(txt))

        if paths:
            for p in paths:
                name = os.path.basename(p)
                with open(p, 'rb') as rfile:
                    part = MIMEBase('application', "octet-stream")
                    part.set_payload(rfile.read())
                    part['Content-Disposition'] = 'attachment; filename="{}"'.format(name)
                    msg.attach(part)
        return msg

# ============= EOF =============================================
