#===============================================================================
# Copyright 2011 Jake Ross
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



#=============enthought library imports=======================
from traits.api import HasTraits, Any, Float, List, Instance, Bool
from traitsui.api import View, Item, Group, TabularEditor
from traitsui.tabular_adapter import TabularAdapter

#=============standard library imports ========================
from numpy import vstack
#=============local library imports  ==========================


class DataItem(HasTraits):
    '''
    '''
    x = Float
    y = Float
    status = Bool(True)


class Adapter(TabularAdapter):
    '''
        
    '''
    columns = [('X', 'x'), ('Y', 'y')]

    # DataItem_x_image=Property
    def get_bg_color(self, obj, name, row):
        '''

        '''
        if not obj.trait_get(name)[name][row].status:
            return 'red'

    def get_format(self, obj, trait, row, column):
        '''

        '''
        return '%0.3f'
#    def _get_DataItem_x_image(self):
#        if not self.item.status:
#            return '@icons:red_ball'


class DataEditor(HasTraits):
    '''
    '''
    graph = Any
    adapter = Instance(Adapter)

    def __init__(self, *args, **kw):
        '''

        '''
        super(DataEditor, self).__init__(*args, **kw)
        self._build_()

    def _adapter_default(self):
        '''
        '''
        return Adapter()

    def _build_(self):
        '''
        '''
        n = self.graph.get_num_plots()
        for i in range(n):
            n, obj = self._table_factory(i)
            self.add_trait(n, obj)

    def _table_factory(self, _id):
        '''
        '''
        name = 'table%i' % _id

        plot = self.graph.plots[_id].plots['plot0'][0]

        x = plot.index.get_data()
        y = plot.value.get_data()
        data = vstack((x, y)).transpose()
        data = [DataItem(x=d[0], y=d[1]) for d in data]

        data = List(data)
        return name, data

    def traits_view(self):
        '''
        '''
        content = []
        n = self.graph.get_num_plots()
        if n == 1:
            t = Item('table0', show_label=False, editor=TabularEditor(adapter=self.adapter))
            content.append(t)
        else:
            for i in range(n):
                t = Item('table%i' % i, show_label=False, editor=TabularEditor(adapter=self.adapter),
                   label='Table %i' % i)
                content.append(t)
        return View(Group(content=content, layout='tabbed'))


class RegressionDataItem(DataItem):
    '''
    '''
    res = Float


class RegressionAdapter(Adapter):
    def __init__(self, *args, **kw):
        '''
        '''
        super(RegressionAdapter, self).__init__(*args, **kw)
        self.columns.append(('Res.', 'res'))


class RegressionDataEditor(DataEditor):
    '''
    '''

    def _adapter_default(self):
        '''
        '''
        return RegressionAdapter()

    def _build_(self):
        '''
        '''
        n = self.graph.get_num_plots()

        for i in range(n):
            name, data = self._table_factory(i)
            if name in self.traits().keys():
                self.trait_set(**{name: data})
            else:
                self.add_trait(name, List(data))

    def _load_table(self, id_):
        '''
        '''
        x, y, res = self.graph.calc_residuals(plotid=id_)
        data = vstack((x, y, res)).transpose()
        data = [RegressionDataItem(x=d[0], y=d[1], res=d[2]) for d in data]

        s = self.graph.plots[id_].plots['plot0'][0].index.metadata.get('selections')

        for si in s:
            data[si].status = False
        return data

    def _table_factory(self, i):
        '''
        '''
        name = 'table%i' % i
        data = self._load_table(i)
        return name, data
#============= EOF =====================================
