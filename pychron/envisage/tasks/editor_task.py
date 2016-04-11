# ===============================================================================
# Copyright 2013 Jake Ross
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
from pyface.tasks.api import IEditor, IEditorAreaPane
from pyface.tasks.task_layout import PaneItem, Splitter
from traits.api import Property, Instance

# ============= standard library imports ========================
import os
# ============= local library imports  ==========================
from pychron.envisage.tasks.advanced_editor_area_pane import myAdvancedEditorAreaPane
from pychron.envisage.tasks.base_task import BaseManagerTask, BaseExtractionLineTask


class BaseEditorTask(BaseManagerTask):
    active_editor = Property(Instance(IEditor),
                             depends_on='editor_area.active_editor')
    editor_area = Instance(IEditorAreaPane)

    def set_editor_layout(self, layout):
        ea = self.editor_area
        ea.set_layout(layout)

    def split_editors(self, a, b, h1=-1, h2=-1, orientation='horizontal'):
        layout = Splitter(PaneItem(id=a, height=h1),
                          PaneItem(id=b, height=h2),
                          orientation=orientation)
        self.set_editor_layout(layout)

    def db_save_info(self):
        self.information_dialog('Changes saved to the database')

    def get_editor(self, name, key='name'):
        return next((e for e in self.editor_area.editors if getattr(e, key) == name), None)

    def get_editor_names(self):
        return [e.name for e in self.editor_area.editors]

    def iter_editors(self, klass):
        return (e for e in self.editor_area.editors if isinstance(e, klass))

    def has_active_editor(self, klass=None):
        if not self.active_editor:
            self.information_dialog('No active tab. Please open a tab')
        elif klass:
            if not isinstance(self.active_editor, klass):
                name = str(klass).split('.')[-1][:-2].replace('Editor', '')
                self.information_dialog('No active tab. Please open a "{}" tab'.format(name))
                return

        return self.active_editor

    def get_editors(self, klass):
        return (ei for ei in self.editor_area.editors if isinstance(ei, klass))

    def close_editor(self, editor):
        self.editor_area.remove_editor(editor)

    def activate_editor(self, editor):
        if self.editor_area:
            try:
                self.editor_area.activate_editor(editor)
            except AttributeError:
                pass

    def create_central_pane(self):
        # self.editor_area = AdvancedEditorAreaPane()
        self.editor_area = myAdvancedEditorAreaPane()
        return self.editor_area

    def open(self, path=None, **kw):
        """
            Shows a dialog to open a file.
        """
        if path is None or not os.path.isfile(path):
            path = self.open_file_dialog()

        if path:
            return self._open_file(path, **kw)
        else:
            self._open_abort()

    def save(self, path=None):
        """
            if the active_editor doesnt have a path e.g not yet saved
            do a save as
        """
        if self.active_editor:
            if not path:
                if self.active_editor.path:
                    path = self.active_editor.path

            if not path:
                path = self.save_file_dialog()

            if path:
                if self._save_file(path):
                    self.active_editor.dirty = False
                    self.active_editor.path = path

    def new(self):
        pass

    def save_as(self):
        kw = {}
        df = self._generate_default_filename()
        if df:
            kw['default_filename'] = df
        path = self.save_file_dialog(**kw)
        if path:
            if self._save_file(path):
                self.active_editor.path = path
                self.active_editor.dirty = False
                return True

    def close_all(self):
        for e in self.editor_area.editors:
            self.close_editor(e)

    # private
    def _generate_default_filename(self):
        return

    def _save_file(self, path):
        pass

    def _open_file(self, path, **kw):
        pass

    def _open_abort(self):
        pass

    def _pre_open_hook(self):
        pass

    def _open_editor(self, editor, activate=True, **kw):
        if self.editor_area:
            if editor not in self.editor_area.editors:
                self.editor_area.add_editor(editor)
                if activate:
                    self.editor_area.activate_editor(editor)

    def _get_active_editor(self):
        if self.editor_area is not None:
            return self.editor_area.active_editor

        return None

    def _prompt_for_save(self):
        if self.editor_area is None:
            return True

        dirty_editors = dict([(editor.name, editor)
                              for editor in self.editor_area.editors
                              if editor.dirty])
        if not dirty_editors:
            return True

        message = 'You have unsaved files. Would you like to save them?'
        ret = self._handle_prompt_for_save(message)
        if ret == 'save':
            for _, editor in dirty_editors.items():
                editor.save(editor.path)

        return ret


class EditorTask(BaseExtractionLineTask, BaseEditorTask):
    pass

# ============= EOF =============================================
