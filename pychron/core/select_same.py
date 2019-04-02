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
from traits.api import HasTraits, List
from traitsui.api import UItem, CheckListEditor

from pychron.core.helpers.traitsui_shortcuts import okcancel_view


class SelectSameMixin(HasTraits):
    default_attr = None

    def select_same_attr(self):
        hs = self._get_selection_attrs()
        ev = SelectAttrView(available_attributes=hs)
        ev.on_trait_change(self._handle_select_attributes, 'attributes')
        ev.edit_traits()

    def _handle_select_attributes(self, attributes):
        if attributes:
            s = self.selected[0]

            def test(v):
                return all([getattr(v, k) == getattr(s, k) for k in attributes])

            self._select_same(test)

    def select_same(self):
        self._select_same(self._default_test())

    def _select_same(self, test):
        self.selected = [si for si in self._get_records() if test(si)]

    def _get_records(self):
        raise NotImplementedError

    def _get_selection_attrs(self):
        raise NotImplementedError

    def _default_test(self):
        v = getattr(self.selected[0], self.default_attr)

        def test(si):
            return getattr(si, self.default_attr) == v

        return test


class SelectAttrView(HasTraits):
    attributes = List
    available_attributes = List

    def traits_view(self):
        v = okcancel_view(UItem('attributes', style='custom',
                                editor=CheckListEditor(name='available_attributes',
                                                       cols=3)),
                          title='Select Attributes')
        return v

# ============= EOF =============================================
