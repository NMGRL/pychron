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
from traits.api import HasTraits, List, Str, Int, Button, Property, Instance, \
    Event
from traitsui.api import View, Item, Controller, TabularEditor, UItem, spring, HGroup, VSplit, VGroup, InstanceEditor
from traitsui.tabular_adapter import TabularAdapter
# ============= standard library imports ========================
from datetime import datetime
# ============= local library imports  ==========================
from pychron.envisage.icon_button_editor import icon_button_editor
from pychron.git_archive.diff_view import DiffView
from pychron.git_archive.utils import GitShaObject


class CommitAdapter(TabularAdapter):
    columns = [('Message', 'message'),
               ('Date', 'date')]
    message_width = Int(300)


# class GitShaObject(HasTraits):
#     message = Str
#     date = Date
#     blob = Str
#     name = Str
#     hexsha = Str
#     author = Str
#     email = Str
#     active = Bool
#
#     def traits_view(self):
#         return View(UItem('blob',
#                           style='custom',
#                           editor=TextEditor(read_only=True)))




class BaseGitHistory(HasTraits):
    items = List
    selected = Instance(GitShaObject)
    head_hexsha = Str

    def set_items(self, items, auto_select=True):
        factory = self.git_sha_object_factory
        self.items = [factory(c) for c in items]
        if auto_select:
            self.selected = self.items[0]

    def git_sha_object_factory(self, com):
        return GitShaObject(hexsha=com.hexsha,
                            message=com.message,
                            active=com.hexsha == self.head_hexsha,
                            date=datetime.fromtimestamp(float(com.committed_date)))


class GitArchiveHistory(BaseGitHistory):
    checkout_button = Button('Checkout')
    diff_button = Button
    limit = Int(100, enter_set=True, auto_set=False)

    diffable = Property(depends_on='selected')
    checkoutable = Property(depends_on='selected')
    checkout_event = Event
    diff_klass = DiffView
    auto_commit_checkouts = True

    selected = List
    selected_commit = Property(depends_on='selected')

    repo_man = Instance('pychron.git_archive.repo_manager.GitRepoManager')
    _path = Str

    def __init__(self, path=None, root=None, *args, **kw):
        super(BaseGitHistory, self).__init__(*args, **kw)
        if root:
            from pychron.git_archive.repo_manager import GitRepoManager

            self.repo_man = GitRepoManager()
            self.repo_man.open_repo(root)

        if path:
            self._path = path

    def close(self):
        pass
        # self.repo_man.close()

    def load_history(self, p=None):
        if p is None:
            p = self._path

        if p:
            self._path = p
            hx = self.repo_man.commits_iter(p, keys=['message', 'committed_date'],
                                            limit=self.limit)
            self.items = [GitShaObject(hexsha=a, message=b,
                                       date=datetime.utcfromtimestamp(c),
                                       name=p) for a, b, c in hx]

    def _selected_changed(self, new):
        if new:
            new = new[-1]
            if not new.blob:
                new.blob = self.repo_man.unpack_blob(new.hexsha, new.name)

    def _get_selected_commit(self):
        if self.selected:
            return self.selected[-1]

    def _limit_changed(self):
        self.load_history()

    def _checkout_button_fired(self):
        with open(self._path, 'w') as wfile:
            wfile.write(self.selected_commit.blob)

        if self.auto_commit_checkouts:
            self.repo_man.add(self._path,
                              msg_prefix='checked out')
            self.load_history()

        self.selected = self.items[:1]
        self.checkout_event = self._path

    def _diff_button_fired(self):
        a, b = self.selected
        d = self.repo_man.diff(a.hexsha, b.hexsha)
        if not a.blob:
            a.blob = self.repo_man.unpack_blob(a.hexsha, a.name)

        if not b.blob:
            b.blob = self.repo_man.unpack_blob(b.hexsha, b.name)

        ds = '\n'.join([li for li in d.split('\n')
                        if li[0] in ('-', '+')])

        lm = a.message
        n = 40
        if len(lm) > n:
            lm = '{}...'.format(lm[:n])

        rm = a.message
        if len(rm) > n:
            rm = '{}...'.format(rm[:n])

        dd = self.diff_klass(left=a.blob, left_date=a.date.strftime('%m-%d-%Y %H:%M:%S'), left_message=lm,
                             right=b.blob, right_date=b.date.strftime('%m-%d-%Y %H:%M:%S'), right_message=rm,
                             diff=ds)

        dd.edit_traits()
        # dd.configure_traits()

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
        v = View(VGroup(HGroup(spring, Item('limit')),
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
                 width=400, height=400,
                 title=self.title,
                 resizable=True)
        return v

# if __name__ == '__main__':
# r = '/Users/ross/Sandbox/gitarchive'
# gh = GitArchiveHistory(r, '/Users/ross/Sandbox/ga_test.txt')
#
# gh.load_history('ga_test.txt')
# ghv = GitArchiveHistoryView(model=gh)
#     ghv.configure_traits(kind='livemodal')
# ============= EOF =============================================
