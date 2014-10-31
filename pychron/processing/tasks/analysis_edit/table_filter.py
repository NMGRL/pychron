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
from pychron.core.ui import set_toolkit
from pychron.envisage.icon_button_editor import icon_button_editor


set_toolkit('qt4')


#============= enthought library imports =======================
from traits.api import HasTraits, Button, List, Str, Float, \
    Either, Bool, on_trait_change, Int, Property, Event
from traitsui.api import View, Item, UItem, EnumEditor, HGroup, \
    ListEditor, InstanceEditor, VGroup, spring, VSplit, Handler

#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.processing.tasks.analysis_edit.adapters import UnknownsAdapter
from pychron.core.ui.tabular_editor import myTabularEditor
from pychron.core.ui.custom_label_editor import CustomLabel


class Filter(HasTraits):
    parameter = Str
    parameters = List(['Age', 'Age Error', 'Aliquot', 'Step'])
    comparator = Str
    comparators = List(['<', '>', '>=', '<=', 'not =', 'between'])

    criterion = Either(Float, Str('E'))
    secondary_criterion = Either(Float, Str('K'))

    removable = Bool(False)
    add_button = Button
    remove_button = Button

    def apply_filter(self, items, omit):
        func = self._assemble_filter_func()
        if omit:
            n=0
            for i in items:
                if func(i):
                    i.table_filter_omit = True
                    n+=1
            return items, n
        else:
            ns= filter(func, items)
            return ns, len(items)-len(ns)

    def _assemble_filter_func(self):
        def convert_crit(c):
            if isinstance(c, str):
                c = '"{}"'.format(c)
            return c

        def convert_parameter(p):
            p = p.lower()
            if p == 'age error':
                p = 'age_err'
            return p

        def func(x):
            comp = self.comparator
            if comp == 'not =':
                comp = '!='

            if comp == 'between':
                a, b = self.criterion, self.secondary_criterion
                if a > b:
                    b, a = self.criterion, self.secondary_criterion

                rule = '{}<=x<={}'.format(convert_crit(a),
                                          convert_crit(b))
            else:
                rule = 'x{}{}'.format(comp, convert_crit(self.criterion))

            p = convert_parameter(self.parameter)
            return eval(rule, {'x': getattr(x, p)})

        return func

    def traits_view(self):
        v = View(HGroup(spring,
                        icon_button_editor('add_button', 'add'),
                        icon_button_editor('remove_button', 'delete', visible_when='removable'),
                        UItem('parameter', editor=EnumEditor(name='parameters')),
                        UItem('comparator', editor=EnumEditor(name='comparators')),
                        UItem('criterion'),
                        UItem('secondary_criterion', visible_when='comparator=="between"')))
        return v


class TableFilterHandler(Handler):
    def revert(self, info):
        info.object.filtered = False
        info.object._nfiltered = 0


class TableFilter(HasTraits):
    apply_filter_button = Button
    items = List
    filters = List
    filtered = Bool(False)

    nitems = Property(depends_on='_nfiltered, items[]')
    nfiltered = Property(depends_on='_nfiltered')
    _nfiltered = Int
    omit = Bool(False)
    refresh_needed = Event

    def _get_nitems(self):
        n=len(self.items)
        if self.omit:
            n-=self._nfiltered

        return 'Analyses= {}'.format(n)

    def _get_nfiltered(self):
        return 'Filtered= {}'.format(self._nfiltered)

    def _filters_default(self):
        return [Filter(criterion=10, comparator='>', parameter='Age Error')]

    @on_trait_change('filters:[add_button,remove_button]')
    def _handle_add_remove(self, obj, name, old, new):
        if name == 'add_button':
            idx = self.filters.index(obj) + 1
            self.filters.insert(idx, Filter(removable=True, criterion=''))
        else:
            self.filters.remove(obj)

    def _apply_filter_button_fired(self):
        self.apply_filter()

    def apply_filter(self):
        items = self.items
        o = len(items)
        nf=0

        for i in items:
            i.table_filter_omit=False

        for fi in self.filters:
            items, filtered = fi.apply_filter(items, self.omit)
            nf+=filtered

        self._nfiltered = nf
        self.items = items
        self.filtered = True
        self.refresh_needed = True

    def traits_view(self):
        v = View(VSplit(VGroup(UItem('filters', editor=ListEditor(editor=InstanceEditor(),
                                                                  mutable=False,
                                                                  style='custom')),
                               HGroup(spring, UItem('apply_filter_button', label='Apply Filters'),
                                      Item('omit', label='Omit', tooltip='Omit analyses instead of exclude'))),
                        VGroup(HGroup(CustomLabel('nitems', color='maroon'),
                                      CustomLabel('nfiltered', color='green')),
                               UItem('items', editor=myTabularEditor(adapter=UnknownsAdapter(),
                                                                     refresh='refresh_needed')))),
                 resizable=True,
                 handler=TableFilterHandler(),
                 buttons=['OK', 'Cancel', 'Revert'],
                 height=500, width=500,
                 title='Filter Analyses'
        )
        return v


if __name__ == '__main__':
    tf = TableFilter()
    tf.configure_traits()
#============= EOF =============================================
