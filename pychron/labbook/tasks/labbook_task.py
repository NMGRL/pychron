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
from pyface.tasks.action.task_action import TaskAction
from pyface.tasks.task_layout import PaneItem, TaskLayout
from traits.api import HasTraits, Button, Str, Int, Bool, Instance, Any, Event
from traitsui.api import View, Item, UItem, HGroup, VGroup
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.core.helpers.filetools import max_path_cnt
from pychron.core.helpers.iterfuncs import partition
from pychron.core.hierarchy import Hierarchy, FilePath
from pychron.core.progress import open_progress
from pychron.envisage.resources import icon
from pychron.envisage.tasks.base_task import BaseTask
from pychron.envisage.tasks.editor_task import BaseEditorTask
from pychron.git_archive.git_archive import GitArchive
from pychron.git_archive.repo_manager import GitRepoManager
from pychron.labbook.tasks.note_editor import NoteEditor
from pychron.labbook.tasks.panes import NotesBrowserPane
from pychron.paths import paths


class AddNoteAction(TaskAction):
    name = 'Add Note'
    method = 'add_note'
    image = icon('add')


class SaveNoteAction(TaskAction):
    name = 'Save Note'
    method = 'save_note'
    image = icon('save')


class AddFolderAction(TaskAction):
    name = 'Add Folder'
    method = 'add_folder'
    image = icon('add')


class NewNameView(HasTraits):
    name = Str
    message = Str

    def traits_view(self):
        v = View(UItem('message', style='readonly', width=1.0),
                 UItem('name'),
                 title='New Folder Name',
                 width=300,
                 buttons=['OK', 'Cancel'])
        return v


class LabbookTask(BaseEditorTask):
    tool_bars = [SToolBar(AddNoteAction(),
                          SaveNoteAction()),
                 SToolBar(AddFolderAction())]

    remote = Str
    _repo = Instance(GitRepoManager)
    hierarchy = Instance(Hierarchy, ())
    selected_root = Any
    dclicked = Event

    # tasks protocol
    def activated(self):
        repo = GitRepoManager()
        repo.open_repo(paths.labbook_dir)
        self._repo = repo

        self._preference_binder('pychron.labbook', ('remote',))

        self.remote = ''
        if self.remote:
            remote = 'https://github.com/{}'.format(self.remote)
            self._repo.create_remote(remote)
            self._remote_action('Pulling', self._repo.pull)

        self.make_hierarchy()

    def prepare_destroy(self):
        if self.remote:
            self._remote_action('Pushing', self._repo.push)

    def make_hierarchy(self):
        root = paths.labbook_dir

        dirs, files = self._make_paths(root)
        self.hierarchy = Hierarchy(name='Labbook',
                                   root_path=root, children=dirs + files)
        for di in dirs:
            self._load_hierarchy(di, levels=3)

        # print 'asdadasfs --------'
        # self.hierarchy.pwalk()

    def _make_paths(self, root):

        xs = [xi for xi in os.listdir(root) if not xi.startswith('.')]

        dirs, files = partition(xs, lambda x: not os.path.isfile(os.path.join(root, x)))

        files = [self._child_factory(ci) for ci in files]
        dirs = [self._directory_factory(di) for di in dirs]
        return dirs, files

    def _directory_factory(self, name):
        return Hierarchy(name=name)

    def _child_factory(self, name):
        return FilePath(name=name)

    def _load_hierarchy(self, obj, levels=None, level=0):
        print 'loading h for {}  levels={}/{}'.format(obj.path, level, levels)
        dirs, files = self._make_paths(obj.path)
        obj.children = dirs + files

        if levels and level == levels:
            return

        # print [ci.path for ci in obj.children]
        for di in dirs:
            self._load_hierarchy(di,level=level + 1, levels=levels)

    # def _on_click(self, obj, **kw):
    #     if isinstance(obj, Hierarchy):
    #         self._load_hierarchy(obj)

    def _dclicked_fired(self):
        root = self.selected_root.path
        if os.path.isfile(root):
            # name = os.path.relpath(root, paths.labbook_dir)

            editor = NoteEditor()
            editor.load(root)
            self._open_editor(editor)

    # def _selected_root_changed(self, new):
    #     if new:
    #         print new, new.make_path()

    def create_dock_panes(self):
        return [NotesBrowserPane(model=self)]

    # action handlers
    def add_folder(self):
        d = self.selected_root.path
        if os.path.isdir(d):
            p = self.get_new_name(d, os.path.isdir)
            if p:
                os.mkdir(p)
                self.make_hierarchy()

    def get_new_name(self, root, test):

        e = NewNameView()
        while 1:
            info = e.edit_traits(kind='livemodal')
            if info.result:
                p = os.path.join(root, e.name)
                if not test(p):
                    return p
                    # os.mkdir(p)
                    # self.make_hierarchy()
                    # break
                else:
                    e.message = '{} already exists'.format(e.name)
            else:
                break

    def save_note(self):
        if self.has_active_editor():

            p=self.get_new_name(self.active_editor.root, os.path.isfile)
            if p:
                self.active_editor.save(p)
                self._repo.add(p, msg=self.active_editor.commit_message,
                               msg_prefix='',
                               commit=True)
                self.make_hierarchy()

    def add_note(self):
        names = self.get_editor_names()

        if self.selected_root and self.selected_root.path!=paths.labbook_dir:
            root = self.selected_root.path
            offset = max_path_cnt(root, 'Note_', extension='')
            name = 'Note {:03n}'.format(len(names) + offset)
            name = os.path.join(os.path.relpath(root, paths.labbook_dir),name)
        else:
            root = paths.labbook_dir
            offset = max_path_cnt(root, 'Note_', extension='')
            name = 'Note {:03n}'.format(len(names) + offset)

        editor = NoteEditor(default_name=name, root=root)

        self._open_editor(editor)

    #private
    def _remote_action(self, name, action):
        msg = '{} changes to {}'.format(name, self.remote)
        prog = open_progress(n=10, message=msg)

        action()
        prog.close()

    def _default_layout_default(self):
        return TaskLayout(left=PaneItem('pychron.labbook.browser'))

# ============= EOF =============================================



