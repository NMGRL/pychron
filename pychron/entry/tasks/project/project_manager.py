# ===============================================================================
# Copyright 2016 ross
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

# ============= standard library imports ========================
from traits.api import List, Str, Dict, Button, Int, String, Event

from pychron.core.fuzzyfinder import fuzzyfinder
from pychron.envisage.browser.record_views import ProjectRecordView
from pychron.loggable import Loggable


class ProjectManager(Loggable):
    oitems = List
    items = List

    filter_str = Str(enter_set=True, auto_set=False)
    filter_attrs = Dict({'name': 'Name',
                         'unique_id': 'UniqueID',
                         'principal_investigator': 'Principal Investigator',
                         'lab_contact': 'Lab Contact'})
    filter_attr = Str

    # add_button = Button
    # ir = Str
    # institution = Str
    # comment = String
    # pi = Str
    # lab_contact = Str
    # pis = List
    # lab_contacts = List

    scroll_to_row = Int
    comment = String
    selected = List
    save_button = Button
    refresh = Event

    def activated(self):
        with self.dvc.session_ctx(use_parent_session=False):
            self.items = self.oitems = [ProjectRecordView(pr) for pr in self.dvc.get_projects()]

            # self._filter()

            # self.pis = self.dvc.get_principal_investigator_names()
            # self.lab_contacts = self.dvc.get_usernames()

    # def prepare_destroy(self):
    #     self.dvc.close_session()

    # private
    # def _add(self):
    #     self.dvc.add_ir(self.pi, self.lab_contact,
    #                     ir=self.ir,
    #                     comment=self.comment,
    #                     institution=self.institution)
    #
    #     self.oitems = self.dvc.get_irs()
    #     self._filter()
    def _comment_changed(self, new):
        if self.selected:
            for i in self.selected:
                i.comment = new
                if new != i.db_comment:
                    i.comment = new
                    i.dirty = True
                else:
                    i.dirty = False
            self.refresh = True

    def _save_button_fired(self):
        self.debug('Apply changes')
        dvc = self.dvc
        with dvc.session_ctx(use_parent_session=False):
            for item in self.oitems:
                if item.dirty:
                    pr = dvc.get_project_by_id(item.unique_id)
                    pr.comment = item.comment
                    item.dirty = False

    def _filter(self):
        if self.filter_str:
            self.items = fuzzyfinder(self.filter_str, self.oitems, self.filter_attr)
        else:
            self.items = self.oitems
        self.scroll_to_row = len(self.items) - 1

    def _filter_str_changed(self):
        self._filter()

    def _filter_attr_changed(self):
        self._filter()

        # def _add_button_fired(self):
        #     self._add()

# ============= EOF =============================================
