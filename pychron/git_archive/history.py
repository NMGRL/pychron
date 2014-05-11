#===============================================================================
# Copyright 2014 Jake Ross
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#===============================================================================
from datetime import datetime

from pychron.core.ui import set_qt


set_qt()
#============= enthought library imports =======================
from traitsui.tabular_adapter import TabularAdapter
from traits.api import HasTraits, List, Str, Instance, Date, Int, Button
from traitsui.api import View, Item, Controller, TextEditor, \
    TabularEditor, UItem, spring, HGroup, VSplit, VGroup
#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.git_archive.git_archive import GitArchive


class CommitAdapter(TabularAdapter):
    columns = [('Message', 'message'),
               ('Date', 'date')]
    message_width = Int(300)


class Commit(HasTraits):
    message = Str
    date = Date
    blob = Str
    name = Str

    def traits_view(self):
        return View(UItem('blob',
                          style='custom',
                          editor=TextEditor(read_only=True)))


class GitArchiveHistory(HasTraits):
    items = List
    selected = Instance(Commit)
    checkout_button = Button('Checkout')
    limit = Int(100, enter_set=True, auto_set=False)

    _archive = GitArchive
    _checkout_path = Str

    _loaded_history_path = None

    def __init__(self, root, cho, *args, **kw):
        super(GitArchiveHistory, self).__init__(*args, **kw)
        self._archive = GitArchive(root)
        self._checkout_path = cho

    def close(self):
        self._archive.close()

    def load_history(self, p=None):
        if p is None:
            p = self._loaded_history_path

        if p:
            self._loaded_history_path = p
            hx = self._archive.commits_iter(p, keys=['message', 'committed_date'],
                                            limit=self.limit)
            self.items = [Commit(hexsha=a, message=b,
                                 date=datetime.utcfromtimestamp(c),
                                 name=p) for a, b, c in hx]

    def _limit_changed(self):
        self.load_history()

    def _selected_changed(self, new):
        if new:
            if not new.blob:
                new.blob = self._archive.unpack_blob(new.hexsha, new.name)

    def _checkout_button_fired(self):
        with open(self._checkout_path, 'w') as fp:
            fp.write(self.selected.blob)

        self._archive.add(self._checkout_path,
                          message_prefix='checked out')
        self.load_history()
        self.selected = self.items[0]


class GitArchiveHistoryView(Controller):
    model = GitArchiveHistory
    title = Str

    def closed(self, info, is_ok):
        self.model.close()

    def traits_view(self):
        v = View(VGroup(
            HGroup(spring, Item('limit')),
            VSplit(UItem('items',
                         height=0.75,
                         editor=TabularEditor(adapter=CommitAdapter(),
                                              selected='selected')),
                   UItem('selected',
                         height=0.25,
                         style='custom')),
            HGroup(spring, UItem('checkout_button', enabled_when='selected'))),

                 kind='livemodal',
                 width=400,
                 height=400,
                 title=self.title,
                 resizable=True)
        return v


if __name__ == '__main__':
    r = '/Users/ross/Sandbox/gitarchive'
    gh = GitArchiveHistory(r, '/Users/ross/Sandbox/ga_test.txt')

    gh.load_history('ga_test.txt')
    ghv = GitArchiveHistoryView(model=gh)
    ghv.configure_traits()
#============= EOF =============================================

