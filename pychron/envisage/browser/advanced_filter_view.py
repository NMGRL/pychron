# ===============================================================================
# Copyright 2017 ross
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
from __future__ import absolute_import
from traits.api import HasTraits, List, Button, Str, Enum, Bool, on_trait_change
from traitsui.api import View, UItem, Item, VGroup, InstanceEditor, ListEditor, EnumEditor, HGroup
from uncertainties import nominal_value, std_dev

from pychron.envisage.icon_button_editor import icon_button_editor


class SQLFilter(HasTraits):
    attribute = Str
    comparator = Enum('=', '<', '>', '<=', '>=', '!=', 'between', 'not between')
    criterion = Str
    attributes = List

    chain_operator = Enum('and', 'or')
    show_chain = Bool(True)
    remove_button = Button
    remove_visible = Bool(True)

    # _eval_func = None

    # def __init__(self, txt=None, *args, **kw):
    #     super(PipelineFilter, self).__init__(*args, **kw)
    #     if txt:
    #         self.parse_string(txt)

    # def generate_evaluate_func(self):
    #     def func(edict):
    #         attr = self.attribute
    #         comp = self.comparator
    #         crit = self.criterion
    #
    #         # val = self._get_value(item, attr)
    #         # edict = {attr: val}
    #
    #         attr = attr.replace(' ', '_')
    #
    #         if comp == '=':
    #             comp = '=='
    #
    #         if comp in ('between', 'not between'):
    #
    #             try:
    #                 low, high = crit.split(',')
    #             except ValueError:
    #                 return
    #
    #             if comp == 'between':
    #                 test = '{}<{}<{}'.format(low, attr, high)
    #             else:
    #                 test = '{}>{} or {}>{}'.format(low, attr, attr, high)
    #         else:
    #             test = '{}{}{}'.format(attr, comp, crit)
    #
    #         try:
    #             result = eval(test, edict)
    #         except (AttributeError, ValueError):
    #             result = False
    #
    #         return result
    #
    #     self._eval_func = func
    #
    # def evaluate(self, item):
    #     attr = self.attribute
    #     val = self._get_value(item, attr)
    #     attr = attr.replace(' ', '_')
    #     edict = {attr: val}
    #     return self._eval_func(edict)
    #
    # def _get_value(self, item, attr):
    #     if attr in ('age', 'age error'):
    #         val = getattr(item, 'uage')
    #         val = nominal_value(val) if attr == 'age' else std_dev(val)
    #     else:
    #         val = getattr(item, attr)
    #
    #     return val

    def traits_view(self):
        v = View(HGroup(icon_button_editor('remove_button', 'delete', visible_when='remove_visible'),
                        UItem('chain_operator', visible_when='show_chain'),
                        UItem('attribute',
                              editor=EnumEditor(name='attributes')),
                        UItem('comparator'),
                        UItem('criterion')))
        return v


class AdvancedFilterView(HasTraits):
    filters = List
    add_filter_button = Button
    attributes = List(['age', 'age_error'])

    def demo(self):
        self.filters = [SQLFilter(comparator='<',
                                  attribute='Ar40',
                                  remove_visible=False,
                                  show_chain=False,
                                  criterion='55'),
                        SQLFilter(comparator='<',
                                  attribute='Ar39',
                                  chain='and',
                                  criterion='55')]

    @on_trait_change('filters:remove_button')
    def _handle_remove(self, obj, name, old, new):
        self.filters.remove(obj)

    def _filters_default(self):
        return [SQLFilter(remove_visible=False,
                          show_chain=False, attributes=self.attributes)]

    def _add_filter_button_fired(self):
        self.filters.append(SQLFilter(attributes=self.attributes))

    def _filters_items_changed(self):
        for i, fi in enumerate(self.filters):
            fi.show_chain = i != 0

    def traits_view(self):
        v = View(VGroup(icon_button_editor('add_filter_button', 'add'),
                        UItem('filters', editor=ListEditor(mutable=False,
                                                           style='custom',
                                                           editor=InstanceEditor()))),
                 kind='livemodal',
                 title='Advanced Search',
                 resizable=True,
                 width=700,
                 height=350,
                 buttons=['OK', 'Cancel'])
        return v


if __name__ == '__main__':
    d = AdvancedFilterView()
    d.configure_traits()
# ============= EOF =============================================
