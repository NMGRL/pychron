# ===============================================================================
# Copyright 2014 Jake Ross
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
from pychron.core.ui import set_qt
set_qt()

# ============= enthought library imports =======================
from traits.api import HasTraits, Button, Str, Bool, List, String
from traitsui.api import View, UItem, TableEditor, HGroup, VSplit, Handler, VGroup
from pyface.message_dialog import information
# ============= standard library imports ========================
import os
# ============= local library imports  ==========================
from traitsui.extras.checkbox_column import CheckboxColumn
from traitsui.table_column import ObjectColumn
from pychron.envisage.tasks.pane_helpers import icon_button_editor


class ModifiedPath(HasTraits):
    use=Bool(True)
    path=Str
    name=Str
    directory=Str

    def __init__(self, path, *args, **kw):
        super(ModifiedPath, self).__init__(*args, **kw)
        self.name=os.path.basename(path)
        self.directory=os.path.dirname(path)
        self.path = path


class CommitDialogHandler(Handler):
    def close( self, info, is_ok ):
        print 'asdf', info.object, info.object.commit_message

        if is_ok and not info.object.commit_message:
            information(None, 'Please enter a commit message')
            return False

        return True


class CommitDialog(HasTraits):
    paths = List
    toggle_use = Button
    commit_message = String
    _use_state = Bool(True)
    selected= List

    def __init__(self, ps, *args, **kw):
        super(CommitDialog, self).__init__(*args, **kw)
        self.paths = sorted((ModifiedPath(pp) for pp in ps),
                            key=lambda x: x.directory)

    def _toggle_use_fired(self):
        rows = self.paths
        if self.selected:
            rows =self.selected
            func=lambda x: not x.use
        else:
            self._use_state =not self._use_state
            func=lambda x: self._use_state

        for ri in rows:
            ri.use = func(ri)

    def traits_view(self):
        cols = [CheckboxColumn(name='use'),
                ObjectColumn(name='name'),
                ObjectColumn(name='directory')]

        v = View(VGroup(HGroup(icon_button_editor('toggle_use','check')),
                VSplit(UItem('paths',
                       editor=TableEditor(columns=cols,
                                          selection_mode='rows',
                                          selected='selected',
                                          editable=False,
                                          sortable=False, deletable=False)),
                 UItem('commit_message', style='custom'))),
                 resizable=True,
                 buttons=['OK','Cancel'],
                 title='Select Files to Commit',
                 kind='livemodal',
                 handler=CommitDialogHandler())
        return v

    def valid_paths(self):
        return [pp for pp in self.paths if pp.use]

#============= EOF =============================================



