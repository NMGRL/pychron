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
from __future__ import absolute_import
from apptools.preferences.preference_binding import bind_preference
from traits.api import Instance, Bool, List

# ============= standard library imports ========================
from datetime import datetime
import socket

# ============= local library imports  ==========================
from pychron.version import __version__
from pychron.experiment.notifier.templates import email_template
from pychron.loggable import Loggable


class ExperimentNotifier(Loggable):
    emailer = Instance("pychron.social.email.emailer.Emailer")
    include_log = Bool

    def __init__(self, *args, **kw):
        super(ExperimentNotifier, self).__init__(*args, **kw)
        bind_preference(self, "include_log", "pychron.experiment.include_log")

    def notify(self, ctx, subject):
        mctx = self._assemble_ctx(**ctx)

        self.debug(
            "Notify with context={}".format(
                {k: v for k, v in mctx.items() if k != "log"}
            )
        )
        message = email_template(**mctx)

        user_email = ctx.get("user_email")
        if user_email:
            self.info(
                "Notifying user={} email={}".format(ctx.get("username"), user_email)
            )
            subject = "{} {}".format(subject, datetime.now().isoformat())
            self._send(user_email, subject, message)

        if ctx.get("use_group_email"):
            pairs = ctx.get("group_emails")
            if pairs:
                names, addrs = pairs
                self.info("Notifying user group names={}".format(",".join(names)))
                self._send(addrs, subject, message)

    def start_queue(self, ctx):
        if ctx.get("use_email") or ctx.get("use_group_email"):
            subject = 'Experiment "{}" Started'.format(ctx.get("experiment_name"))
            self.notify(ctx, subject)

    def end_queue(self, ctx):
        if ctx.get("use_email") or ctx.get("use_group_email"):
            tag = "Finished"
            if ctx.get("err_message"):
                tag = "Stopped"
            elif ctx.get("canceled"):
                tag = "Canceled"

            subject = 'Experiment "{}" {}'.format(ctx.get("experiment_name"), tag)
            self.notify(ctx, subject)

    def _send(self, address, subject, msg):
        # self.debug('Subject= {}'.format(subject))
        # self.debug('Body= {}'.format(msg))
        if self.emailer:
            if not self.emailer.send(address, subject, msg):
                self.warning("email server not available")
                return True
        else:
            self.unique_warning("email plugin not enabled")
            return True

    def _assemble_ctx(self, **kw):
        log = ""
        if self.include_log:
            log = self._get_log(500)

        shorthost = socket.gethostname()
        ip4host = socket.gethostbyname(shorthost).split(".")[-1]
        ctx = {
            "timestamp": datetime.now(),
            "log": log,
            "host": ".{}".format(ip4host),
            "shorthost": shorthost,
            "version": __version__,
        }

        ctx.update(kw)
        return ctx

    def _get_log(self, n):
        from pychron.core.helpers.logger_setup import get_log_text

        return get_log_text(n) or "No log available"


# ============= EOF =============================================
