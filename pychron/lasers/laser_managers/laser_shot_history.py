# ===============================================================================
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
# ===============================================================================



#========== future imports ====================
from __future__ import with_statement

#============= enthought library imports =======================
from traits.api import HasTraits, List, Property, Str, Int, Float, Button, Enum
from traitsui.api import View, Item, Group, TableEditor
from traitsui.table_column import ObjectColumn
import apptools.sweet_pickle as pickle
#============= standard library imports ========================
import os
import shutil
#============= local library imports  ==========================
from pychron.paths import paths
from pychron.core.helpers.filetools import unique_path
from pychron.core.helpers.datetime_tools import generate_datetimestamp

#============= views ===================================
class LaserShot(HasTraits):
    '''
    '''
    id = Int
    mode = Enum('single', 'continuous')
    timestamp = Str
    energy = Float


class LaserShotHistory(HasTraits):
    '''
        G{classtree}
    '''
    pickle_path = Str
    history = List(LaserShot)
    dump = Button
    clear = Button
    count = Property(depends_on='history')
    view_mode = Enum('detail', 'simple')

    def __init__(self, *args, **kw):
        '''
            @type *args: C{str}
            @param *args:

            @type **kw: C{str}
            @param **kw:
        '''
        super(LaserShotHistory, self).__init__(*args, **kw)
        if not self.pickle_path:
            self.pickle_path = os.path.join(paths.root, '.laser_shot_history')
        self.load()

    def _get_count(self):
        '''
        '''
        return len(self.history)

    def _dump_fired(self):
        '''
        '''
        self.__dump()

    def _clear_fired(self):
        '''
        '''
        self.__clear()

    def __dump(self):
        '''
        '''
        with open(self.pickle_path, 'w') as f:
            pickle.dump(self.history, f)
    def load(self):
        '''
        '''
        if os.path.isfile(self.pickle_path):
            with open(self.pickle_path, 'r') as f:
                self.history = pickle.load(f)
    def __clear(self):
        '''
        '''
        # make a backup copy
        p, _cnt = unique_path(paths.root, 'laser_shot_history', 'bak')
        shutil.copy(self.pickle_path, p)

        os.remove(self.pickle_path)
        self.history = []

    def add_shot(self, **kw):
        '''
            @type **kw: C{str}
            @param **kw:
        '''
        n = len(self.history)

        shot = LaserShot(id=n,
                       timestamp=generate_datetimestamp(),
                       **kw)
        self.history.append(shot)
        self.__dump()

    def traits_view(self):
        '''
        '''

        cols = [ObjectColumn(name='id'),
              ObjectColumn(name='mode'),
              ObjectColumn(name='timestamp')]
        table_editor = TableEditor(columns=cols,
                                 editable=False)
        detail_view = Group(Item('dump', show_label=False),
                          Item('clear', show_label=False),
                          Item('history', editor=table_editor,
                               show_label=False),
                         visible_when='view_mode=="detail"',
                         )
        simple_view = Group(Item('count'),
                          visible_when='view_mode=="simple"')
        v = View(detail_view,
               simple_view)


        return v
#============= EOF ====================================
