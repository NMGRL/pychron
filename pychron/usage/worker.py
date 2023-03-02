# ===============================================================================
# Copyright 2022 ross
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


import os
import time
import datetime

import requests
from pyface.message_dialog import warning
from traits.trait_types import Bool, Str

from pychron.core.helpers.logger_setup import logging_setup
from pychron.core.progress import progress_iterator, progress_loader, open_progress
from pychron.core.ui.gui import invoke_in_main_thread
from pychron.core.ui.preference_binding import bind_preference
from pychron.loggable import Loggable
from pychron.paths import paths

try:
    from google.cloud import storage

    # from google.oauth2.credentials import Credentials
    from google.oauth2 import service_account
except ImportError:
    warning(
        None,
        "Necessary library not installed please install Google Cloud Storage Client\n\n"
        "pip install --upgrade google-cloud-storage",
    )
    storage = None


class UsageWorker(Loggable):
    # share_setupfiles_enabled = Bool
    # share_scripts_enabled = Bool
    lab_name = Str

    def __init__(self, bind=True, *args, **kw):
        super(UsageWorker, self).__init__(*args, **kw)
        if bind:
            # bind_preference(self, 'share_setupfiles_enabled', 'pychron.usage.share_setupfiles_enabled')
            # bind_preference(self, 'share_scripts_enabled', 'pychron.usage.share_scripts_enabled')
            bind_preference(self, "lab_name", "pychron.general.lab_name")
        self.ignore = [".DS_Store", ".git"]

    def share(self, share_scripts=True, share_setupfiles=True):
        self.debug("usage sharing")
        lab_name = self.lab_name
        if not lab_name:
            self.warning_dialog("Please set a lab_name in Preference/General")
            return

        # self.setup_working_repo()
        client = self.get_client()
        if client:
            self.debug("share setupfiles")
            try:
                if share_setupfiles:
                    self.share_setupfiles(client)
            except BaseException:
                self.debug("Failed sharing setupfiles")
                self.debug_exception()

            self.debug("share scripts")
            try:
                if share_scripts:
                    self.share_scripts(client)
            except BaseException as e:
                print(e)
                self.debug("failed sharing scripts")
                self.debug_exception()

            self.debug("sharing complete")
        else:
            self.warning_dialog(
                "Failed to get Google Storage Client. Cannot share configuration. see log for more "
                "details"
            )

    # @property
    # def workingroot(self):
    #     return os.path.join(paths.hidden_dir, 'usage', self.lab_name)

    def get_client(self):
        try:
            p = os.path.join(paths.hidden_dir, "pychronlabs_usage_service_account.json")
            if os.path.isfile(p):
                creds = service_account.Credentials.from_service_account_file(p)
                client = storage.Client(project="pychronlabs", credentials=creds)
            else:
                self.debug(f"File {p} does not exist")
        except BaseException:
            self.debug_exception()
            return

        return client

    # def setup_working_repo(self):
    #     workingroot = self.workingroot
    #     if not os.path.isdir(workingroot):
    #         os.mkdir(workingroot)
    #
    #     self.repo_manager = GitRepoManager()
    #     self.repo_manager.init_repo(workingroot)

    def share_setupfiles(self, client):
        self._share_directory(client, paths.setup_dir, "setupfiles")

    def share_scripts(self, client):
        self._share_directory(client, paths.scripts_dir, "scripts")

    def _share_directory(self, client, root, tag):
        ps = list(self._gen_paths(root))
        n = len(ps)
        prog = open_progress(n)
        bucket = client.get_bucket("pychronlabs_usage")
        with requests.Session() as session:
            for i, (src, dest) in enumerate(ps):
                dest = "{}/{}/{}".format(self.lab_name, tag, dest)
                blob = bucket.blob(dest)
                url = blob.generate_signed_url(
                    version="v4",
                    # This URL is valid for 15 minutes
                    expiration=datetime.timedelta(minutes=15),
                    # Allow PUT requests using this URL.
                    method="PUT",
                    content_type="application/octet-stream",
                )
                with open(src, "r") as rfile:
                    resp = session.put(
                        url,
                        headers={"Content-Type": "application/octet-stream"},
                        data=rfile.read(),
                    )
                    self.debug(
                        "{} status_code={}".format(
                            os.path.basename(dest), resp.status_code
                        )
                    )
                prog.change_message("Uploading {} {}/{} {}".format(tag, i, n, dest))

    def _gen_paths(self, baseroot):
        for root, dirs, files in os.walk(baseroot):
            # print(root, dirs, files)
            if os.path.basename(root) == ".git":
                continue

            for f in files:
                if f in self.ignore:
                    continue

                src = os.path.join(root, f)
                # dest = src.replace(baseroot, self.workingroot)
                dest = os.path.relpath(src, baseroot)
                yield src, dest


if __name__ == "__main__":
    paths.build("~/Pychron")
    logging_setup("pychron", level="DEBUG")
    u = UsageWorker(bind=False)
    u.lab_name = "NMGRLFoo"
    # u.share_setupfiles_enabled = True
    # u.share_scripts_enabled = True
    # u.configure_traits()
    u.share()
# ============= EOF =============================================
