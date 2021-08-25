# ===============================================================================
# Copyright 2021 ross
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
from traits.api import HasTraits, List, Str, Dict, Bool
from traitsui.api import HGroup, Item, VGroup

from pychron.core.helpers.traitsui_shortcuts import okcancel_view
from pychron.core.pychron_traits import EmailStr
from pychron.core.ui.combobox_editor import ComboboxEditor


class GitCommitAuthorView(HasTraits):
    author = Str
    authors = List
    authornames = List
    email = EmailStr
    remember_choice = Bool

    def __init__(self, *args, **kw):
        super(GitCommitAuthorView, self).__init__(*args, **kw)
        self.authornames = [a.name for a in self.authors]

    def _author_changed(self, new):
        if new and new in self.authornames:
            a = next((aa for aa in self.authors if aa.name == new), None)
            self.email = a.email

    def traits_view(self):
        v = okcancel_view(VGroup(Item('author', editor=ComboboxEditor(name='authornames')),
                                 Item('email')),
                          Item('remember_choice', label='Remember this choice?'),
                          width=400,
                          title='Git Commit Author')
        return v

# ============= EOF =============================================
