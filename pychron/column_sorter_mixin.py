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

#============= enthought library imports =======================
from traits.api import HasTraits, Any
#============= standard library imports ========================
#============= local library imports  ==========================

class ColumnSorterMixin(HasTraits):
    _sort_field = None
    _reverse_sort = False
    column_clicked = Any

    def _column_clicked_changed(self, event):
        values = event.editor.value
        name, field = event.editor.adapter.columns[event.column]
        self._reverse_sort = not self._reverse_sort

        self._sort_columns(values, name, field)

    def _sort_columns(self, values, name='', field=None):
        # get the field to sort on
        if field is None:
            field = self._sort_field
            if field is None:
                return

        skey = '_{}_{}_sort_key'.format(name.lower(), field.lower())
        if hasattr(self, skey):
            key = getattr(self, skey)
        else:
            key = lambda x: getattr(x, field)

        values.sort(key=key,
                    reverse=self._reverse_sort)
        self._sort_field = field

# ============= EOF =============================================
