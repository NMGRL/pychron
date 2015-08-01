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
import os

from pyface.tasks.action.schema import SToolBar
from pyface.tasks.task_layout import PaneItem, TaskLayout, Tabbed
from traits.api import Button, Str, Bool, \
    Instance, Any, Event, on_trait_change, Enum

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.core.helpers.filetools import modified_datetime, created_datetime, max_file_cnt
from pychron.core.helpers.iterfuncs import partition
from pychron.core.hierarchy import Hierarchy, FilePath
from pychron.core.progress import open_progress
from pychron.envisage.tasks.actions import ToggleFullWindowAction
from pychron.envisage.tasks.editor_task import BaseEditorTask
from pychron.git_archive.history import GitArchiveHistory
from pychron.git_archive.repo_manager import GitRepoManager
from pychron.labbook.labeler import Labeler
from pychron.labbook.tasks.actions import AddNoteAction, SaveNoteAction, AddFolderAction, PullAction, PushAction, \
    NewLabelAction
from pychron.labbook.tasks.note_editor import NoteEditor
from pychron.labbook.tasks.panes import NotesBrowserPane, FileHistoryPane, LabelPane
from pychron.labbook.tasks.views import get_posts
from pychron.paths import paths


class LabBookTask(BaseEditorTask):
    name = 'LabBook'
    tool_bars = [SToolBar(AddNoteAction(),
                          SaveNoteAction()),
                 SToolBar(AddFolderAction()),
                 SToolBar(PushAction(),
                          PullAction()),
                 SToolBar(NewLabelAction()),
                 SToolBar(ToggleFullWindowAction())]

    remote = Str
    _repo = Instance(GitRepoManager)
    hierarchy = Instance(Hierarchy, ())
    history_model = Instance(GitArchiveHistory, ())
    selected_root = Any
    dclicked = Event
    chronology_visible = Bool(False)
    filter_hierarchy_str = Str  # (auto_set=False, enter_set=True)
    filter_by_date_button = Button
    date_filter = Enum('Modified', 'Created')

    labeler = Instance(Labeler, ())
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
            self._repo.create_remote(remote, force=True)
            self.pull(make=False)

        self.make_hierarchy()

        self._repo.add(os.path.join(paths.labbook_dir, 'labels.db'))

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
                FileHistoryPane(model=self.history_model),
                LabelPane(model=self.labeler)]

    # action handlers
    def new_label(self):
        if self.labeler.new_label():
            self.debug('new label added')

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

    def save_note(self, save_as=True):
        if self.has_active_editor():
            if not self.active_editor.dirty:
                return

            p = None
            if not save_as:
                p = self.active_editor.path

            if not p:
                p = self.get_new_name(self.active_editor.root,
                                      os.path.isfile, 'New Note Name',
                                      name=os.path.basename(self.active_editor.name))

            if p:
                self.active_editor.save(p)
                self._repo.add(p, commit=False)
                self._repo.commit_dialog()
                self.make_hierarchy()

    def add_note(self):
        names = self.get_editor_names()

        if isinstance(self.selected_root, Hierarchy) and \
                        self.selected_root.path != paths.labbook_dir:
            root = self.selected_root.path
            # offset = max_path_cnt(root, 'Note ', delimiter=' ', extension='')
            # name = 'Note {:03n}'.format(len(names) + offset)
            # name = os.path.join(os.path.relpath(root, paths.labbook_dir), name)
            nfunc = lambda name: os.path.join(os.path.relpath(root, paths.labbook_dir), name)
        else:
            root = paths.labbook_dir
            nfunc = lambda name: name
            # offset = max_path_cnt(root, 'Note ', delimiter=' ', extension='')

        offset = max_file_cnt(root, excludes=['README.md'])
        name = 'Note {:03d}'.format(offset)
        while name in names:
            offset += 1
            name = 'Note {:03d}'.format(offset)

        name = nfunc(name)
        editor = NoteEditor(default_name=name, root=root)

        self._open_editor(editor)

    # handlers
    @on_trait_change('labeler:label_event')
    def _handle_label_event(self, new):
        if self.active_editor:
            if self.active_editor.path:
                path = os.path.relpath(self.active_editor.path, paths.labbook_dir)
                self.labeler.set_label(path, new)
                self.active_editor.set_label(new)

    def _active_editor_changed(self, new):
        if new:
            try:
                self.history_model.load_history(new.path)
            except Exception, e:
                print 'exception', e
                self.debug('failed loading file history for {}'.format(new.path))

            labels = self.labeler.load_labels_for_path(os.path.relpath(new.path, paths.labbook_dir))

            new.labels = labels

    def _dclicked_fired(self):
        if self.selected_root:
            root = self.selected_root.path
            if os.path.isfile(root):
                name = os.path.relpath(root, paths.labbook_dir)
                for a in self.editor_area.editors:
                    if a.name == name:
                        self.activate_editor(a)
                        return
                else:
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


    @on_trait_change('history_model:checkout_event')
    def _handle_checkout(self):
        self.active_editor.load()

    def _date_filter_changed(self):
        if self._post_view:
            self.make_hierarchy(*self._post_view.posts)

    # private
    def _prompt_for_save(self):
        ret = super(LabBookTask, self)._prompt_for_save()
        if ret and self._repo.is_dirty():
            ret = self._handle_prompt_for_save('You have uncommitted changes. Would you like to commit them?')
            if ret == 'save':
                return self._repo.commit_dialog()

        return ret

    def _get_commit_message(self):
        return 'default commit message'

    def _auto_cleanup(self):
        m = self._get_commit_message()
        self._repo.cmd('add', '--all', '.')
        self._repo.commit(m)

    _post_view = None

    def _get_posts(self):
        self._post_view, posts = get_posts(self._post_view, self.hierarchy.chronology)
        return posts

    def _make_paths(self, root, lpost=None, hpost=None):
        xs = [xi for xi in os.listdir(root) if not xi.startswith('.')]

        dirs, files = partition(xs, lambda x: not os.path.isfile(os.path.join(root, x)))

        if self.filter_hierarchy_str:
            files = (ci for ci in files if ci.startswith(self.filter_hierarchy_str))

        if self.date_filter == 'Modified':
            func = modified_datetime
        else:
            func = created_datetime

        if lpost:
            try:
                lpost = lpost.date()
            except AttributeError:
                pass
            files = (ci for ci in files
                     if func(os.path.join(root, ci), strformat=None).date() >= lpost)

        if hpost:
            try:
                hpost = hpost.date()
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
                          right=Tabbed(PaneItem('pychron.labbook.labels'),
                                       PaneItem('pychron.labbook.file_history')))

# ============= EOF =============================================



