# ===============================================================================
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
# ===============================================================================

# ============= enthought library imports =======================
from __future__ import absolute_import

from traits.api import Any, Event

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.pipeline.plot.editors.base_editor import BaseEditor


class BaseTableEditor(BaseEditor):
    selected = Any
    refresh_needed = Event
    basename = 'table'

    # def save_file(self, p, title=''):
    #     if p.endswith('.xls'):
    #         self.make_xls_table(title, p)
    #     elif p.endswith('.pdf'):
    #         self.make_pdf_table(title, p)
    #     else:
    #         self.make_csv_table(title, p)
    #
    # def clean_rows(self):
    #     return self._clean_items()
    #
    # def _clean_items(self):
    #     return [x for x in self.items if not isinstance(x, (TableBlank, TableSeparator))]
    #
    # def _get_save_path(self, path, ext='.pdf'):
    #     if path is None:
    #         dlg = FileDialog(action='save as', default_directory=paths.processed_dir)
    #         if dlg.open():
    #             if dlg.path:
    #                 path = add_extension(dlg.path, ext)
    #
    #     return path

# ============= EOF =============================================
