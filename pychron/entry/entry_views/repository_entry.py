# ===============================================================================
# Copyright 2015 Jake Ross
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
from traits.api import Str, List, Enum, Bool
from traitsui.api import VGroup, UItem, Item, EnumEditor

from pychron.core.pychron_traits import BorderHGroup
from pychron.core.ui.strings import SpacelessStr, RepoNameStr
from pychron.entry.entry_views.entry import BaseEntry, OKButton, STYLESHEET

LICENSES = {
    "GNU General Public License v3.0": "gpl-3.0",
    "Apache 2.0": "apache-2.0",
    "Creative Commons Attribution 4.0": "cc-by-4.0",
    "Academic Free License v3.0": "afl-3.0",
}


class RepositoryIdentifierEntry(BaseEntry):
    tag = "Repository Identifier"
    principal_investigator = Str
    principal_investigators = List
    value = RepoNameStr
    readme = Str
    license_template_name = Enum(LICENSES.keys())
    private = Bool(True)

    def _add_item(self):
        with self.dvc.session_ctx(use_parent_session=False):
            if self.dvc.check_restricted_name(
                self.value, "repository_identifier", check_principal_investigator=False
            ):
                self.error_message = "{} is a restricted!.".format(self.value)
                if not self.confirmation_dialog(
                    "{} is a restricted!.\n Are you certain you want to add this "
                    "Repository?".format(self.value)
                ):
                    return

            if not self.principal_investigator:
                self.information_dialog("You must select a Principal Investigator")
                return

            ret = True

            template = LICENSES.get(self.license_template_name)
            if not template:
                template = "gpl-3.0"

            if not self.dvc.add_repository(
                self.value,
                self.principal_investigator,
                license_template=template,
                private=self.private,
            ):
                ret = False
                if not self.confirmation_dialog(
                    'Could not add "{}". Try a different name?'.format(self.value)
                ):
                    ret = None
            else:
                self.dvc.add_readme(self.value, self.readme)

        return ret

    def traits_view(self):
        # style_sheet='QLabel {font-size: 10px} QLineEdit {font-size: 10px}'

        a = VGroup(
            Item("value", label="Repository Name"),
            Item(
                "principal_investigator",
                editor=EnumEditor(name="principal_investigators"),
            ),
            BorderHGroup(UItem("readme", style="custom"), label="ReadMe"),
            Item("license_template_name", label="License"),
            Item("private", label="Private", tooltip="Use a private repo"),
            UItem("error_message", style="readonly", style_sheet=STYLESHEET),
        )
        buttons = [OKButton(), "Cancel"]
        return self._new_view(
            a, width=400, title="Add {}".format(self.tag), buttons=buttons
        )


if __name__ == "__main__":
    d = RepositoryIdentifierEntry()
    d.configure_traits()

# ============= EOF =============================================
