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
from pyface.file_dialog import FileDialog
from traits.api import List, Any, Event, Bool

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.envisage.tasks.base_editor import grouped_name, BaseTraitsEditor
from pychron.pipeline.editors.base_adapter import TableBlank, TableSeparator
from pychron.core.helpers.filetools import add_extension
from pychron.paths import paths


class BaseTableEditor(BaseTraitsEditor):
    items = List
    records = List
    # oitems = List
    col_widths = List
    selected = Any
    refresh_needed = Event
    use_alternating_background = Bool(False)

    basename = 'table'

    def save_file(self, p, title=''):
        if p.endswith('.xls'):
            self.make_xls_table(title, p)
        elif p.endswith('.pdf'):
            self.make_pdf_table(title, p)
        else:
            self.make_csv_table(title, p)

    def set_items(self, items):
        self.items = items

    def _items_changed(self):
        self._set_name()

    def _set_name(self):
        na = list(set([ni.sample for ni in self.items]))
        na = grouped_name(na)
        self.name = '{} {}'.format(na, self.basename)

    def clean_rows(self):
        return self._clean_items()

    def _clean_items(self):
        return filter(lambda x: not isinstance(x, (TableBlank, TableSeparator)),
                      self.items)

    def _get_save_path(self, path, ext='.pdf'):
        if path is None:
            dlg = FileDialog(action='save as', default_directory=paths.processed_dir)
            if dlg.open():
                if dlg.path:
                    path = add_extension(dlg.path, ext)

        return path

    def make_pdf_table(self, *args, **kw):
        pass

    def make_xls_table(self, *args, **kw):
        pass

    def make_csv_table(self, *args, **kw):
        pass

# ============= EOF =============================================
