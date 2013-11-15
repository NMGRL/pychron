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



#============= enthought library imports ======================
from traits.api import HasTraits, List, CStr, Button
from traitsui.api import View, Item, HGroup, spring, TabularEditor
from traitsui.tabular_adapter import TabularAdapter
from pyface.file_dialog import FileDialog
from pyface.constant import OK

#============= standard library imports =======================

#============= local library imports  =========================
from pychron.paths import paths
from pychron.hardware.axis import Axis
from pychron.loggable import Loggable


class Result(HasTraits):
    name = CStr
    key = CStr
    result = CStr

    def __init__(self, name, key, result, *args, **kw):
        super(Result, self).__init__(*args, **kw)
        self.name = name
        self.key = key
        self.result = result

    def tostring(self):
        return '{:<50}{:<10}{:<10}\n'.format(self.name,
                                                 self.key,
                                                 self.result
                                                 )


class ResultsAdapter(TabularAdapter):

    columns = [('Name', 'name'),
             ('Key', 'key'),
             # ('Command', 'cmd'),
             ('Result', 'result')
             ]

    def get_width(self, obj, trait, column):
        w = -1
        if column == 0:
            w = 290
        return w


class ResultsReport(Loggable):
    results = List
    save = Button
    axis = Axis

    def _save_fired(self):
        dlg = FileDialog(default_directory=paths.root_dir,
                         action='save as'
                         )
        if dlg.open() == OK:
            self.info('saving results to {}'.format(dlg.path))
            with open(dlg.path, 'w') as f:
                f.write('name = {} id = {}\n'.format(self.axis.name, self.axis.id))
                for r in self.results:
                    f.write(r.tostring())

    def add(self, *args):
        self.results.append(Result(*args))

    def traits_view(self):

        self.results = sorted(self.results, key=lambda r: r.key)
        v = View(Item('results', show_label=False,
                      style='custom',
                      editor=TabularEditor(adapter=ResultsAdapter(),

                                           editable=False
                                           )
                    ),
                 HGroup(spring, Item('save', show_label=False)),
                 width=550,
                 height=800,
                 resizable=True,
                 title='Results'
                 )
        return v
#============= EOF ===================================
