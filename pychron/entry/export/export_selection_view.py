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
from traits.api import HasTraits, Enum, List, Instance, File, Str, Password, Dict
from traitsui.api import View, Item, UItem, VGroup, InstanceEditor, ListStrEditor
# ============= standard library imports ========================
# ============= local library imports  ==========================
from traitsui.tabular_adapter import TabularAdapter


class IrradiationAdapter(TabularAdapter):
    columns = [('Irradiation', 'name')]


class BaseExportDestination(HasTraits):
    def to_dict(self):
        pass


class FileDestination(BaseExportDestination):
    path = File

    def to_dict(self):
        return {'path': self.path}

    def traits_view(self):
        v = View(Item('path'))
        return v


class XMLDestination(FileDestination):
    pass


class YAMLDestination(FileDestination):
    pass


class XLSDestination(FileDestination):
    pass


class MassSpecDestination(BaseExportDestination):
    name = Str
    host = Str
    username = Str
    password = Password

    def to_dict(self):
        return {attr:getattr(self, attr) for attr in ('name','host','username','password')}

    def traits_view(self):
        v = View(VGroup(Item('name'),
                        Item('host'),
                        Item('username'),
                        Item('password')))
        return v


class ExportSelectionView(HasTraits):
    export_type = Enum('MassSpec', 'XML', 'YAML', 'XLS')
    irradiations = List
    export_destination = Instance(BaseExportDestination)
    default_massspec_connection = Dict
    selected = List

    def __init__(self, *args, **kw):
        super(ExportSelectionView, self).__init__(*args, **kw)
        self._export_type_changed()

    @property
    def destination_dict(self):
        return self.export_destination.to_dict()

    def _export_type_changed(self):
        dest = globals()['{}Destination'.format(self.export_type)]
        d = dest()
        if self.export_type == 'MassSpec':
            d.trait_set(**self.default_massspec_connection)

        self.export_destination = d

    def traits_view(self):
        v = View(VGroup(UItem('export_type'),
                        VGroup(UItem('export_destination',
                                     style='custom',
                                     editor=InstanceEditor()),
                               label='Destination', show_border=True),
                        UItem('irradiations',
                              editor=ListStrEditor(selected='selected',
                                                   multi_select=True))),
                 buttons=['OK','Cancel'],
                 resizable=True)
        return v


if __name__ == '__main__':
    esv = ExportSelectionView()
    esv.configure_traits()
# ============= EOF =============================================



