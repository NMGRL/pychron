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

from pychron.core.ui import set_qt

set_qt()
#============= enthought library imports =======================
from traits.api import HasTraits, List, Str, Date, Int, Button, Property
from traitsui.api import View, Item, Controller, TextEditor, \
    TabularEditor, UItem, spring, HGroup, VSplit, VGroup, InstanceEditor, HSplit
from traitsui.tabular_adapter import TabularAdapter
#============= standard library imports ========================
from datetime import datetime
#============= local library imports  ==========================
from pychron.envisage.tasks.pane_helpers import icon_button_editor
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
    hexsha = Str

    def traits_view(self):
        return View(UItem('blob',
                          style='custom',
                          editor=TextEditor(read_only=True)))


class DiffView(HasTraits):
    left = Str
    rigth = Str
    diff = Str

    def traits_view(self):
        return View(VGroup(HSplit(UItem('left',
                                        style='custom',
                                        editor=TextEditor(read_only=True)),
                                  UItem('right',
                                        style='custom',
                                        editor=TextEditor(read_only=True))),
                           UItem('diff',
                                 style='custom',
                                 editor=TextEditor(read_only=True))),
                    title='Diff',
                    width=900,
                    buttons=['OK'],
                    kind='livemodal',
                    resizable=True)


class GitArchiveHistory(HasTraits):
    items = List
    selected = List
    selected_commit = Property(depends_on='selected')
    checkout_button = Button('Checkout')
    diff_button = Button
    limit = Int(100, enter_set=True, auto_set=False)

    _archive = GitArchive
    _checkout_path = Str

    _loaded_history_path = None

    diffable = Property(depends_on='selected')
    checkoutable = Property(depends_on='selected')

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
            new = new[-1]
            if not new.blob:
                new.blob = self._archive.unpack_blob(new.hexsha, new.name)

    def _checkout_button_fired(self):
        with open(self._checkout_path, 'w') as fp:
            fp.write(self.selected.blob)

        self._archive.add(self._checkout_path,
                          message_prefix='checked out')
        self.load_history()
        self.selected = self.items[0]

    def _diff_button_fired(self):
        a, b = self.selected
        d = self._archive.diff(a.hexsha, b.hexsha)
        if not b.blob:
            b.blob = self._archive.unpack_blob(b.hexsha, b.name)

        ds = '\n'.join([li for li in d.split('\n')
                        if li[0] in ('-', '+')])
        dd = DiffView(left=a.blob, right=b.blob, diff=ds)
        dd.edit_traits()

    def _get_selected_commit(self):
        if self.selected:
            return self.selected[-1]

    def _get_diffable(self):
        if self.selected:
            return len(self.selected) == 2

    def _get_checkoutable(self):
        if self.selected:
            return len(self.selected) == 1


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
                                              multi_select=True,
                                              selected='selected')),
                   UItem('selected_commit',
                         editor=InstanceEditor(),
                         height=0.25,
                         style='custom')),
            HGroup(spring, icon_button_editor('diff_button', 'edit_diff',
                                              enabled_when='diffable'),
                   UItem('checkout_button', enabled_when='checkoutable'))),

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
    ghv.configure_traits(kind='livemodal')
#============= EOF =============================================

