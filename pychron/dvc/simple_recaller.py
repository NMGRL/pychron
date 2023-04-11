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

from pychron.core.helpers.traitsui_shortcuts import okcancel_view
from pychron.loggable import Loggable

from traits.api import Str, HasTraits, Int, Directory
from traitsui.api import View, UItem, Item, VGroup


class SimpleDVCRecord(HasTraits):
    uuid = Str
    repository_identifier = Str
    record_id = Str
    group_id = Int
    tag = Str
    load_name = Str
    load_holder = Str
    irradiation = Str
    irradiation_level = Str


class SimpleDVCRecaller(Loggable):
    uuid = Str
    repository_identifier = Str
    repository = Directory

    @property
    def record(self):
        repo = self.repository
        root = os.path.dirname(repo)
        name = os.path.basename(repo)
        return SimpleDVCRecord(
            uuid=self.uuid,
            repository_root=root,
            repository_identifier=name,
            group_id=0,
            tag="OK",
        )

    def traits_view(self):
        v = VGroup(
            Item("uuid"),
            Item("repository"),
        )

        return okcancel_view(
            v, title="Enter Full or Partial UUID", width=500, height=100
        )


# ============= EOF =============================================
