# ===============================================================================
# Copyright 2019 ross
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
from pyface.constant import OK
from pyface.directory_dialog import DirectoryDialog
from pyface.file_dialog import FileDialog
from traits.api import HasTraits

from pychron.paths import paths


class BaseFS(HasTraits):
    def open_file_dialog(self, **kw):
        """
        """
        return self._file_dialog('open', **kw)

    def save_file_dialog(self, **kw):
        """
        """
        return self._file_dialog('save as', **kw)

    def open_directory_dialog(self, **kw):
        return self._directory_dialog(False, **kw)

    def save_directory_dialog(self, **kw):
        return self._directory_dialog(True, **kw)

    # private
    def _directory_dialog(self, new_directory, **kw):
        dlg = DirectoryDialog(new_directory=new_directory, **kw)
        if dlg.open() == OK:
            return dlg.path

    def _file_dialog(self, action, **kw):
        """
        """
        if 'default_directory' not in kw:
            kw['default_directory'] = paths.home

        dlg = FileDialog(action=action, **kw)
        if dlg.open() == OK:
            return dlg.path

# ============= EOF =============================================
