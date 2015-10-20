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

# ============= enthought library imports =======================
from pyface.constant import OK
from pyface.file_dialog import FileDialog
from traits.api import HasTraits, Property, Instance, Str, Button
from traitsui.api import View, Item, HGroup, UItem

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.database.database_connection_spec import DBConnectionSpec


class MassSpecDestination(HasTraits):
    destination = Property
    dbconn_spec = Instance(DBConnectionSpec, ())

    def _get_destination(self):
        return self.dbconn_spec.make_connection_dict()

    def traits_view(self):
        return View(Item('dbconn_spec', show_label=False, style='custom'))

    @property
    def url(self):
        return self.dbconn_spec.make_url()


class PathDestination(HasTraits):
    destination = Str
    browse_button = Button('browse')

    def _browse_button_fired(self):
        dlg = FileDialog(action='save as')
        if dlg.open() == OK:
            self.destination = dlg.path

    def traits_view(self):
        return View(HGroup(UItem('destination', width=0.75),
                           UItem('browse_button', width=0.25)))

    @property
    def url(self):
        return self.destination


class XMLDestination(PathDestination):
    destination = Str('/Users/ross/Sandbox/exporttest2.xml')


class YamlDestination(PathDestination):
    destination = Str('/Users/ross/Sandbox/exporttest2.yaml')


class SQLiteDestination(PathDestination):
    destination = Str('/Users/ross/Sandbox/exporttest2.db')

# ============= EOF =============================================

