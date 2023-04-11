# ===============================================================================
# Copyright 2017 ross
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
from __future__ import absolute_import

import os

from pyface.message_dialog import information
from traits.api import Instance, List, HasTraits, Str, Bool
from traitsui.api import UItem, TableEditor
from traitsui.extras.checkbox_column import CheckboxColumn
from traitsui.table_column import ObjectColumn

from pychron.core.helpers.traitsui_shortcuts import okcancel_view
from pychron.core.yaml import yload
from pychron.paths import paths
from pychron.pipeline.nodes.base import BaseNode

try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    from pychron.social.email.emailer import Emailer
except ImportError:

    class Emailer:
        def send(self, *args, **kw):
            information(
                None,
                "Not all packages that a required to send emails are installed. Please "
                "install the necessary packages. "
                "\n"
                "See https://developers.google.com/gmail/api/quickstart/python",
            )


class Emailee(HasTraits):
    enabled = Bool
    name = Str
    email = Str


class EmailNode(BaseNode):
    name = "Email"
    # emailer = Instance(Emailer)
    emailer = Instance("pychron.social.email.emailer.Emailer")
    addresses = List

    def traits_view(self):
        cols = [
            CheckboxColumn(name="enabled"),
            ObjectColumn(name="name"),
            ObjectColumn(name="email", label="Address"),
        ]

        v = okcancel_view(
            UItem("addresses", editor=TableEditor(columns=cols)),
            title="Configure Email",
        )
        return v

    def configure(self, *args, **kw):
        path = os.path.join(paths.setup_dir, "users.yaml")
        self.addresses = [Emailee(**d) for d in yload(path)]

        return super(EmailNode, self).configure(*args, **kw)

    def run(self, state):
        p = state.report_path
        if p:
            addrs = [e.email for e in self.addresses if e.enabled and e.email]
            sub = "DailyReport"

            msg = "No Report Available"
            if os.path.isfile(p):
                msg = "Daily Report from pychron. See attachment"

            self.emailer.send(
                addrs,
                sub,
                msg,
                paths=[
                    p,
                ],
            )


# ============= EOF =============================================
