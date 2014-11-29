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
from traits.api import HasTraits, Str, Int, Instance, Bool
# ============= standard library imports ========================
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
import socket
# ============= local library imports  ==========================
from pychron.version import __version__
from pychron.experiment.notifier.templates import email_template
from pychron.loggable import Loggable


class Emailer(HasTraits):
    _server = None

    server_username = Str
    server_password = Str
    server_host = Str
    server_port = Int
    include_log = Bool
    sender = Str('pychron@gmail.com')

    def send(self, addr, sub, msg):
        server = self.connect()
        if server:
            msg = self._message_factory(addr, sub, msg)
            try:
                server.sendmail(self.sender, [addr], msg.as_string())
                server.close()
                return True
            except BaseException:
                pass

    def _message_factory(self, addr, sub, txt):
        msg = MIMEMultipart()
        msg['From'] = self.sender  # 'nmgrl@gmail.com'
        msg['To'] = addr
        msg['Subject'] = sub

        msg.attach(MIMEText(txt))
        return msg

    def connect(self):
        if self._server is None:
            try:
                server = smtplib.SMTP(self.server_host, self.server_port)
                server.ehlo()
                server.starttls()
                server.ehlo()

                server.login(self.server_username, self.server_password)
                self._server = server
            except smtplib.SMTPServerDisconnected:
                return
        else:
            self._server.connect(self.server_host, self.server_port)

        return self._server


class UserNotifier(Loggable):
    emailer = Instance(Emailer, ())

    def notify(self, exp, last_runid, err):
        address = exp.email
        if address:
            subject, msg = self._assemble_message(exp, last_runid, err)
            self._notify(address, subject, msg)

    def _notify(self, address, subject, msg):
        # self.debug('Subject= {}'.format(subject))
        # self.debug('Body= {}'.format(msg))
        if not self.emailer.send(address, subject, msg):
            self.warning('email server not available')
            return True

    def notify_group(self, exp, last_runid, err, addrs):
        subject, msg = self._assemble_message(exp, last_runid, err)
        failed = addrs[:]
        for email in addrs:
            if self._notify(email, subject, msg):
                break
            failed.remove(email)

        if failed:
            self.warning('Failed sending notification to emails {}'.join(','.join(failed)))

    def _assemble_message(self, exp, last_runid, err):
        name = exp.name
        if err:
            subject = '{} Canceled'.format(name)
        else:
            subject = '{} Completed Successfully'.format(name)

        ctx = self._assemble_ctx(exp, last_runid, err)
        msg = email_template(**ctx)
        return subject, msg

    def _assemble_ctx(self, exp, last_runid, err):
        log = ''
        if self.emailer.include_log:
            log = self._get_log(100)

        shorthost = socket.gethostname()
        ctx = {'timestamp': datetime.now(),
               'last_runid': last_runid,
               'error': err,
               'log': log,
               'host': socket.gethostbyname(shorthost),
               'shorthost': shorthost,
               'experiment': exp,
               'version': __version__}

        return ctx

    def _get_log(self, n):
        from pychron.core.helpers.logger_setup import get_log_text
        return get_log_text(n) or 'No log available'


if __name__ == '__main__':
    class Exp(object):
        name = 'Foo'
        username = 'root'
        mass_spectrometer = 'jan'
        extract_device = 'co2'
        email = 'jirhiker@gmail.com'
        execution_ratio = '4/5'

    e = Exp()
    a = UserNotifier()
    a.emailer.include_log = True
    sub, msg = a._assemble_message(e, 'adsfafd', 'this is an error\nmultiomasdf')
    for l in msg.split('\n'):
        print l


        # a.notify(e, 'adsfafd', 'this is an error\nmultiomasdf')
# ============= EOF =============================================

