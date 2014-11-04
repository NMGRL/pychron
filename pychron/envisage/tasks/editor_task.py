#===============================================================================
# Copyright 2013 Jake Ross
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

#============= enthought library imports =======================
from pyface import confirmation_dialog
from pyface.constant import NO
from traits.api import Property, Instance
from pyface.tasks.api import IEditor, IEditorAreaPane
#============= standard library imports ========================
import os
#============= local library imports  ==========================
from pychron.envisage.tasks.base_task import BaseManagerTask, BaseExtractionLineTask
from pyface.tasks.advanced_editor_area_pane import AdvancedEditorAreaPane


class myAdvancedEditorAreaPane(AdvancedEditorAreaPane):
    def remove_editor(self, editor):
        """ Removes an editor from the pane.
        """
        editor_widget = editor.control.parent()
        if editor.dirty:
            ret = confirmation_dialog.confirm(editor_widget,
                                              'Unsaved changes to "{}". '
                                              'Do you want to continue'.format(editor.name))
            if ret == NO:
                return

        self.editors.remove(editor)
        self.control.remove_editor_widget(editor_widget)
        editor.editor_area = None
        if not self.editors:
            self.active_editor = None


class BaseEditorTask(BaseManagerTask):
    active_editor = Property(Instance(IEditor),
                             depends_on='editor_area.active_editor')
    editor_area = Instance(IEditorAreaPane)

    def db_save_info(self):
        self.information_dialog('Changes saved to the database')

    def get_editor(self, name):
        return next((e for e in self.editor_area.editors if e.name==name), None)

    def has_active_editor(self, klass=None):
        if not self.active_editor:
            self.information_dialog('No active tab. Please open a tab')
        elif klass:
            if not isinstance(self.active_editor, klass):
                name=str(klass).split('.')[-1][:-2].replace('Editor', '')
                self.information_dialog('No active tab. Please open a "{}" tab'.format(name))
                return

        return self.active_editor

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
        path = self.save_file_dialog()
        if path:
            if self._save_file(path):
                self.active_editor.path = path
                self.active_editor.dirty = False
                return True

    def _save_file(self, path):
        pass

    def _open_file(self, path, **kw):
        pass

    def _open_abort(self):
        pass

    def _pre_open_hook(self):
        pass

    def _open_editor(self, editor, **kw):
        if self.editor_area:
            self.editor_area.add_editor(editor)
            self.editor_area.activate_editor(editor)

            #===============================================================================
            # property get/set
            #===============================================================================

    def _get_active_editor(self):
        if self.editor_area is not None:
            return self.editor_area.active_editor

        return None

    #     def _confirmation(self, message=''):
    #         dialog = ConfirmationDialog(parent=self.window.control,
    #                                     message=message, cancel=True,
    #                                     default=CANCEL, title='Save Changes?')
    #         return dialog.open()

    def _prompt_for_save(self):
        if self.editor_area is None:
            return True
            #return self._handle_prompt_for_save()

        dirty_editors = dict([(editor.name, editor)
                              for editor in self.editor_area.editors
                              if editor.dirty])
        if not dirty_editors.keys():
            return True

        message = 'You have unsaved files. Would you like to save them?'
        ret = self._handle_prompt_for_save(message)
        if ret == 'save':
            for _, editor in dirty_editors.items():
                editor.save(editor.path)

        return ret

        #### Trait change handlers ################################################


class EditorTask(BaseExtractionLineTask, BaseEditorTask):
    pass

#============= EOF =============================================
