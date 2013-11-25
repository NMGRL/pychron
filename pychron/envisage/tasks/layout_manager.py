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

#============= enthought library imports =======================
import shelve
import os

from traits.api import HasTraits, Str, List, Any, Button, on_trait_change
from traitsui.api import View, UItem, TabularEditor, Label, \
    HGroup
from traitsui.tabular_adapter import TabularAdapter

from pychron.paths import paths
from pychron.loggable import Loggable

#============= standard library imports ========================
#============= local library imports  ==========================

class LayoutAdapter(TabularAdapter):
    columns = [('Name', 'name')

               ]

class UserLayout(HasTraits):
    name = Str
    layouts = List

class LayoutManager(Loggable):
    selected = Any
    layouts = List
    new_layout_name = Str
    application = Any
    add_button = Button('+')
    remove_button = Button('-')
    activate_button = Button('Activate')

    def __init__(self, application, *args, **kw):
        self.application = application
        super(LayoutManager, self).__init__(*args, **kw)
        d = self._open_shelve()
        if d:
            for k, v in d.iteritems():
                layout = UserLayout(name=k, layouts=v)
                self.layouts.append(layout)

    @on_trait_change('layouts:name')
    def _update_name(self, obj, name, old, new):
        self.save(remove=old)

    def _activate_button_fired(self):
        app = self.application
        if app:
            for _id, pos, size in self.selected.layouts:

                task = app.get_task(_id)
                if task:
                    win = task.window
                    win.trait_set(position=pos, size=size)
                    win.show(True)

    def _add_button_fired(self):
        self.new_layout()

    def _remove_button_fired(self):
        self.layouts.remove(self.selected)
        self.save(remove=self.selected.name)

    def _assemble_layouts(self):
        app = self.application
        layouts = [(win.active_task.id, win.position, win.size)
                   for win in app.windows]
        return layouts

    def new_layout(self):
        while 1:
            info = self.edit_traits(view='save_view')
            if info.result:
                name = self.new_layout_name
                if not next((li for li in self.layouts if li.name == name), None):
                    layout = UserLayout(name=name,
                                        layouts=self._assemble_layouts()
                                        )
                    self.layouts.append(layout)
                    self.save()
                    break
                else:
                    if not self.confirmation_dialog('Name {} already exists. Choose a different name (Yes/No)?'.format(name)):
                        break

    def save(self, remove=None):
        p = os.path.join(paths.hidden_dir, 'window_positions')
        d = shelve.open(p)
        if remove is not None:
            if d.has_key(remove):
                d.pop(remove)

        for li in self.layouts:
            d[str(li.name)] = li.layouts

        d.close()

    def _open_shelve(self):
        p = os.path.join(paths.hidden_dir, 'window_positions')
        if os.path.isfile(p):
            d = shelve.open(p)
            return d

    def save_view(self):
        v = View(
                 Label('Enter name for new layout'),
                 UItem('new_layout_name'),
                 kind='livemodal',
                 buttons=['OK', 'Cancel'],
                 title='New Window Layout',
                 width=300
                 )
        return v

    def traits_view(self):
        v = View(
                 UItem('layouts',
                       editor=TabularEditor(adapter=LayoutAdapter(),
#                                             editable=False,
                                            selected='selected',
                                            )
                       ),
                 UItem('activate_button', enabled_when='selected'),
                 HGroup(UItem('add_button',),
                        UItem('remove_button', enabled_when='selected'),
                        show_labels=False,
                        ),
                 title='Positions',
                 width=300,
                 buttons=['OK', ]
                 )
        return v


#============= EOF =============================================
