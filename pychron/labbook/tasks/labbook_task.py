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
from datetime import datetime
import os
from pyface.tasks.action.schema import SToolBar
from pyface.tasks.action.task_action import TaskAction
from pyface.tasks.task_layout import PaneItem, TaskLayout
from traits.api import HasTraits, Button, Str, Int, Bool, \
    Instance, Any, Event, on_trait_change, Date, Enum
from traitsui.api import View, Item, UItem, HGroup, VGroup
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.core.helpers.filetools import max_path_cnt, modified_datetime, created_datetime
from pychron.core.helpers.iterfuncs import partition
from pychron.core.hierarchy import Hierarchy, FilePath
from pychron.core.progress import open_progress
from pychron.envisage.resources import icon
from pychron.envisage.tasks.base_task import BaseTask
from pychron.envisage.tasks.editor_task import BaseEditorTask
from pychron.git_archive.git_archive import GitArchive
from pychron.git_archive.history import GitArchiveHistory
from pychron.git_archive.repo_manager import GitRepoManager
from pychron.labbook.tasks.note_editor import NoteEditor
from pychron.labbook.tasks.panes import NotesBrowserPane, FileHistoryPane
from pychron.paths import paths


class AddNoteAction(TaskAction):
    name = 'Add Note'
    method = 'add_note'
    image = icon('note-add')


class SaveNoteAction(TaskAction):
    name = 'Save Note'
    method = 'save_note'
    image = icon('document-save')


class AddFolderAction(TaskAction):
    name = 'Add Folder'
    method = 'add_folder'
    image = icon('folder-new')


class PushAction(TaskAction):
    name = 'Push'
    method = 'push'
    image = icon('arrow_up')


class PullAction(TaskAction):
    name = 'Pull'
    method = 'pull'
    image = icon('arrow_down')


class NewNameView(HasTraits):
    name = Str
    message = Str
    title = Str

    def traits_view(self):
        v = View(UItem('message', style='readonly', width=1.0),
                 UItem('name'),
                 title=self.title,
                 width=300,
                 buttons=['OK', 'Cancel'])
        return v


class PostView(HasTraits):
    low_post = Date
    high_post = Date

    @property
    def posts(self):
        return self.low_post, self.high_post

    def traits_view(self):
        v = View(UItem('low_post', style='custom'),
                 UItem('high_post', style='custom'),
                 title='Select Date Range',
                 width=500,
                 buttons=['OK','Cancel'])
        return v


class LabBookTask(BaseEditorTask):
    tool_bars = [SToolBar(AddNoteAction(),
                          SaveNoteAction()),
                 SToolBar(AddFolderAction()),
                 SToolBar(PushAction(),
                          PullAction())]

    remote = Str
    _repo = Instance(GitRepoManager)
    hierarchy = Instance(Hierarchy, ())
    history_model = Instance(GitArchiveHistory, ())
    selected_root = Any
    dclicked = Event
    chronology_visible = Bool(True)
    filter_hierarchy_str = Str  # (auto_set=False, enter_set=True)
    filter_by_date_button = Button
    date_filter = Enum('Modified','Created')
    # tasks protocol
    def activated(self):
        repo = GitRepoManager()
        repo.open_repo(paths.labbook_dir)
        self._repo = repo
        self.history_model.repo_man = repo
        self.history_model.auto_commit_checkouts = False

        # self._preference_binder('pychron.labbook', ('remote',))

        if self.remote:
            remote = 'https://github.com/{}'.format(self.remote)
            self._repo.create_remote(remote)
            self.pull(make=False)

        self.make_hierarchy()

    def _prompt_for_save(self):
        ret = super(LabBookTask, self)._prompt_for_save()
        if ret and self._repo.is_dirty():
            ret = self._handle_prompt_for_save('You have uncommitted changes. Would you like to commit them?')
            if ret == 'save':
                self._auto_cleanup()
                return True

        return ret

    def _get_commit_message(self):
        return 'default commit message'

    def _auto_cleanup(self):
        m = self._get_commit_message()
        self._repo.cmd('add', '--all', '.')
        self._repo.commit(m)

    def prepare_destroy(self):

        # check for modifications
        if self.remote:
            self._remote_action('Pushing', self._repo.push)

    def make_hierarchy(self, lpost=None, hpost=None):
        root = paths.labbook_dir

        dirs, files = self._make_paths(root, lpost, hpost)
        self.hierarchy = Hierarchy(name='LabBook',
                                   root_path=root,
                                   children=dirs + files)
        for di in dirs:
            self._load_hierarchy(di, levels=3)

    def save(self, path=None):
        self.save_note()

    def save_as(self):
        self.save_note(save_as=True)

    def create_dock_panes(self):
        return [NotesBrowserPane(model=self),
                FileHistoryPane(model=self.history_model)]

    # action handlers
    def push(self):
        if self.remote:
            self._remote_action('Pushing', self._repo.push)

    def pull(self, make=True):
        if self.remote:
            self._remote_action('Pulling', self._repo.pull)
        if make:
            self.make_hierarchy()

    def add_folder(self):
        d = self.selected_root.path
        if os.path.isdir(d):
            p = self.get_new_name(d, os.path.isdir, 'New Folder Name')
            if p:
                os.mkdir(p)
                self.make_hierarchy()

    def get_new_name(self, root, test, title):
        e = NewNameView(title=title)
        while 1:
            info = e.edit_traits(kind='livemodal')
            if info.result:
                # e=e.name.replace(' ','_')
                en = e.name
                p = os.path.join(root, en)
                if not test(p):
                    return p
                else:
                    e.message = '{} already exists'.format(en)
            else:
                break

    def save_note(self, save_as=True):
        if self.has_active_editor():
            if not self.active_editor.dirty:
                return

            if save_as:
                p = self.active_editor.path
                if not p:
                    p = self.get_new_name(self.active_editor.path, os.path.isfile, 'New Note Name')
            else:
                p = self.active_editor.path

            if p:
                self.active_editor.save(p)
                self._repo.add(p, msg=self.active_editor.commit_message,
                               msg_prefix='',
                               commit=True)
                self.make_hierarchy()

    def add_note(self):
        names = self.get_editor_names()

        if self.selected_root and self.selected_root.path != paths.labbook_dir:
            root = self.selected_root.path
            offset = max_path_cnt(root, 'Note_', extension='')
            name = 'Note {:03n}'.format(len(names) + offset)
            name = os.path.join(os.path.relpath(root, paths.labbook_dir), name)
        else:
            root = paths.labbook_dir
            offset = max_path_cnt(root, 'Note_', extension='')
            name = 'Note {:03n}'.format(len(names) + offset)

        editor = NoteEditor(default_name=name, root=root)

        self._open_editor(editor)

    def _active_editor_changed(self, new):
        if new:
            try:
                self.history_model.load_history(new.path)
            except Exception, e:
                print e
                self.debug('failed loading file history for {}'.format(new.path))

    # handlers
    def _dclicked_fired(self):
        if self.selected_root:
            root = self.selected_root.path
            if os.path.isfile(root):
                editor = NoteEditor()
                editor.load(root)
                self._open_editor(editor)

    def _filter_hierarchy_str_changed(self):
        self.make_hierarchy()

    def _filter_by_date_button_fired(self):
        posts = self._get_posts()
        if posts:
            lp, hp = posts
            self.make_hierarchy(lpost=lp, hpost=hp)

    _post_view = None

    def _get_posts(self):
        if not self._post_view:
            pv = PostView()
            chron = self.hierarchy.chronology
            l, h = chron[-1], chron[0]
            fmt = '%m-%d-%Y %H:%M:%S'
            pv.low_post = datetime.strptime(l.create_date, fmt)
            pv.high_post = datetime.strptime(h.create_date, fmt)
            self._post_view = pv

        pv = self._post_view
        info = pv.edit_traits(kind='livemodal')
        if info.result:
            return pv.posts

    @on_trait_change('history_model:checkout_event')
    def _handle_checkout(self):
        self.active_editor.load()

    def _date_filter_changed(self):
        if self._post_view:
            self.make_hierarchy(*self._post_view.posts)

    # private
    def _make_paths(self, root, lpost, hpost):
        xs = [xi for xi in os.listdir(root) if not xi.startswith('.')]

        dirs, files = partition(xs, lambda x: not os.path.isfile(os.path.join(root, x)))

        if self.filter_hierarchy_str:
            files = (ci for ci in files if ci.startswith(self.filter_hierarchy_str))

        if self.date_filter=='Modified':
            func=modified_datetime
        else:
            func=created_datetime

        if lpost:
            try:
                lpost=lpost.date()
            except AttributeError:
                pass
            files = (ci for ci in files
                     if func(os.path.join(root, ci), strformat=None).date() >= lpost)

        if hpost:
            try:
                hpost=hpost.date()
            except AttributeError:
                pass

            files = (ci for ci in files
                     if func(os.path.join(root, ci), strformat=None).date() <= hpost)

        files = [self._child_factory(ci) for ci in files]

        dirs = [self._directory_factory(di) for di in dirs]
        return dirs, files

    def _directory_factory(self, name):
        return Hierarchy(name=name)

    def _child_factory(self, name):
        return FilePath(name=name)

    def _load_hierarchy(self, obj, levels=None, level=0):
        dirs, files = self._make_paths(obj.path)
        obj.children = dirs + files

        if levels and level == levels:
            return

        # print [ci.path for ci in obj.children]
        for di in dirs:
            self._load_hierarchy(di, level=level + 1, levels=levels)

    def _remote_action(self, name, action):
        msg = '{} changes to {}'.format(name, self.remote)
        prog = open_progress(n=10, message=msg)

        action()
        prog.close()

    def _default_layout_default(self):
        return TaskLayout(left=PaneItem('pychron.labbook.browser'),
                          right=PaneItem('pychron.labbook.file_history'))

# ============= EOF =============================================



