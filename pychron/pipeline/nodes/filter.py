# ===============================================================================
# Copyright 2015 Jake Ross
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
from traits.api import HasTraits, Str, Property, List, Enum, Button
from traitsui.api import View, UItem, HGroup, EnumEditor, InstanceEditor
# ============= standard library imports ========================
# ============= local library imports  ==========================
from traitsui.editors import ListEditor
from pychron.envisage.icon_button_editor import icon_button_editor
from pychron.pipeline.nodes.base import BaseNode


class PipelineFilter(HasTraits):
    attribute = Str
    comparator = Enum('<', '>', '<=', '>=', '!=')
    criterion = Str
    attributes = ('uage', 'aliquot', 'step')


    def evaluate(self, item):
        attr = self.attribute
        comp = self.comparator
        crit = self.criterion
        val = getattr(item, attr)
        return eval('{}{}{}'.format(attr, comp, crit), {attr: val})

    def traits_view(self):
        v = View(HGroup(UItem('attribute',
                              editor=EnumEditor(name='attributes')), UItem('comparator'), UItem('criterion')))
        return v

    def to_string(self):
        return '{}{}{}'.format(self.attribute, self.comparator, self.criterion)


class FilterNode(BaseNode):
    name = Property(depends_on='filters')
    analysis_name = 'unknowns'
    filters = List
    add_filter_button = Button

    def _filters_default(self):
        return [PipelineFilter()]

    def _add_filter_button_fired(self):
        self.filters.append(PipelineFilter())

    def traits_view(self):
        v = View(
            icon_button_editor('add_filter_button', 'add'),
            UItem('filters', editor=ListEditor(mutable=False,
                                               style='custom',
                                               editor=InstanceEditor())),
            kind='livemodal',
            buttons=['OK', 'Cancel'])
        return v

    def configure(self):
        info = self.edit_traits()
        if info.result:
            return True

    def _generate_filter(self):
        def func(item):
            for fi in self.filters:
                if fi.evaluate(item):
                    return False
            else:
                return True
                # for attr, comp, crit in self.filters:
                # val = getattr(item, attr)
                # if comp in ('<','>','<=','>=','!='):
                #
                # test = eval('{}{}{}'.format(attr, comp, crit), {attr: val})
                # print test, val, '{}{}{}'.format(attr, comp, crit)
                #         if test:
                #             return False
                # else:
                #     return True

        return func

    def run(self, state):
        vs = filter(self._generate_filter(), getattr(state, self.analysis_name))
        setattr(state, self.analysis_name, vs)

    def add_filter(self, attr, comp, crit):
        self.filters.append(PipelineFilter(attribute=attr, comparator=comp, criterion=crit))

    def _get_name(self):
        return 'Filter ({})'.format(','.join((fi.to_string() for fi in self.filters)))

# ============= EOF =============================================



