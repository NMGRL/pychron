# ===============================================================================
# Copyright 2018 ross
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
from traits.api import List

from pychron.envisage.tasks.base_editor import BaseTraitsEditor, grouped_name


class BaseEditor(BaseTraitsEditor):
    basename = ''
    items = List

    def _items_changed(self):
        self._set_name()

    def set_items(self, items):
        self._set_items(items)

    def _set_items(self, items):
        self.items = items

    def _set_name(self):
        na = sorted(list(set([ni.identifier for ni in self.items])))
        na = grouped_name(na)
        self.name = '{} {}'.format(na, self.basename)


# ============= EOF =============================================
