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

import base64
import mimetypes
import os

# ============= standard library imports ========================
import smtplib
import time
from email.message import EmailMessage
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from apptools.preferences.preference_binding import bind_preference
from pyface.message_dialog import information
from traits.api import HasTraits, Str, Enum, Bool, Int
from traitsui.api import View

try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError

    USE_GMAIL = True
except ImportError:
    USE_GMAIL = False
    information(
        None,
        "Not all packages installed for the email plugin.  Disable Email plugin in "
        "initialization.xml or "
        "install the necessary packages. See https://developers.google.com/gmail/api/quickstart/python",
    )

# ============= local library imports  ==========================
from pychron.loggable import Loggable
from pychron.paths import paths

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
]


class User(HasTraits):
    name = Str
    email = Str
    enabled = Bool
    level = Enum(0, 1, 2)

    telephone = Str

    def edit_view(self):
        return View("name", "email", "level", "telephone")


class Emailer(Loggable):
    server_username = Str
    server_password = Str
    server_host = Str
    server_port = Int

    sender = Str("pychron@gmail.com")
    use_gmail = True

    def __init__(self, bind=True, *args, **kw):
        super(Emailer, self).__init__(*args, **kw)

        self._server = None

        if bind:
            bind_preference(self, "server_username", "pychron.email.server_username")
            bind_preference(self, "server_password", "pychron.email.server_password")
            bind_preference(self, "server_host", "pychron.email.server_host")
            bind_preference(self, "server_port", "pychron.email.server_port")

        if not self.server_port:
            self.server_port = 587

        self.use_gmail = USE_GMAIL

    def test_email_server(self):
        return bool(self.connect(warn=False, test=True)), "No Error Message"

    def connect(self, warn=True, test=False):
        if self.use_gmail:
            creds = None
            # The file token.json stores the user's access and refresh tokens, and is
            # created automatically when the authorization flow completes for the first
            # time.
            token_path = os.path.join(paths.hidden_dir, "token.json")
            if os.path.exists(token_path):
                creds = Credentials.from_authorized_user_file(token_path, SCOPES)
            # If there are no (valid) credentials available, let the user log in.
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    self.information_dialog(
                        "Pychron needs authorization to send emails. You will now be redirected "
                        "to your browser to complete the authorization process"
                    )

                    cred_path = os.path.join(paths.hidden_dir, "credentials.json")
                    flow = InstalledAppFlow.from_client_secrets_file(cred_path, SCOPES)
                    creds = flow.run_local_server(port=0)
                # Save the credentials for the next run
                with open(token_path, "w") as token:
                    token.write(creds.to_json())

            service = None
            try:
                # Call the Gmail API
                service = build("gmail", "v1", credentials=creds)

            except HttpError as error:
                # TODO(developer) - Handle errors from gmail API.
                print(f"An error occurred: {error}")

            return service
        else:
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
                self.debug(
                    "SMTPServer connection err: {}"
                    "host={}, user={}, port={}".format(
                        e, self.server_host, self.server_username, self.server_port
                    )
                )
                if warn:
                    self.warning("SMTPServer not properly configured")
                server = None

            return server

    def send(self, addrs, sub, msg, paths=None):
        self.info("Send email. addrs: {}".format(addrs, sub))

        if "," in addrs:
            addrs = ",".split(addrs)

        st = time.time()
        for i in range(10):
            server = self.connect()
            if server is not None:
                break
            self.debug("doing email connection retry {}".format(i))
            time.sleep(1)
        self.debug("server connection duration={}".format(time.time() - st))

        if server:
            if not isinstance(addrs, (list, tuple)):
                addrs = [addrs]

            if self.use_gmail:
                msg = self._gmail_message_factory(addrs, sub, msg, paths)
                server.users().messages().send(userId="me", body=msg).execute()
            else:
                msg = self._message_factory(addrs, sub, msg, paths)
                try:
                    st = time.time()
                    server.sendmail(self.sender, addrs, msg.as_string())
                    server.quit()
                    self.debug("server.sendmail duration={}".format(time.time() - st))
                    return True
                except BaseException as e:
                    self.warning("Failed sending mail. {}".format(e))
        else:
            self.warning("Failed connecting to server")

    def _gmail_message_factory(self, addrs, sub, msg, paths):
        message = EmailMessage()

        message.set_content(msg)

        message["To"] = ",".join(addrs)
        message["From"] = self.sender
        message["Subject"] = sub
        if paths:
            for p in paths:
                attachment_filename = os.path.basename(p)
                type_subtype, _ = mimetypes.guess_type(attachment_filename)
                maintype, subtype = type_subtype.split("/")

                with open(attachment_filename, "rb") as fp:
                    attachment_data = fp.read()
                message.add_attachment(attachment_data, maintype, subtype)

        # encoded message
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

        return {"raw": encoded_message}

    def _message_factory(self, addrs, sub, txt, paths):
        msg = MIMEMultipart()
        msg["From"] = self.sender  # 'nmgrl@gmail.com'
        msg["To"] = ",".join(addrs)
        msg["Subject"] = sub
        msg.attach(MIMEText(txt))

        if paths:
            for p in paths:
                name = os.path.basename(p)
                with open(p, "rb") as rfile:
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(rfile.read())
                    part["Content-Disposition"] = 'attachment; filename="{}"'.format(
                        name
                    )
                    msg.attach(part)
        return msg


# ============= EOF =============================================
