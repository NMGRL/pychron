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
from traits.api import HasTraits, Str, Bool, List
from traitsui.api import View, UItem, TableEditor, Handler
# ============= standard library imports ========================
# ============= local library imports  ==========================
from traitsui.extras.checkbox_column import CheckboxColumn
from traitsui.table_column import ObjectColumn
import yaml


def boiler_plate(path):
    with open(path, 'w') as fp:
        pass


class User(HasTraits):
    name = Str
    email = Str
    enabled = Bool


class EmailSelectionViewHandler(Handler):
    def closed(self, info, is_ok):
        if is_ok:
            info.object.dump()
        return True


class EmailSelectionView(HasTraits):
    items = List

    def __init__(self, path, *args, **kw):
        super(EmailSelectionView, self).__init__(*args, **kw)
        self.load(path)
        self._path=path

    #persistence
    def dump(self):
        with open(self._path, 'w') as fp:
            yl=[{'name':i.name,'email':i.email, 'enabled':i.enabled} for i in self.items]
            yaml.dump(yl, fp, default_flow_style=False)

    def load(self, path):
        with open(path, 'r') as fp:
            yl = yaml.load(fp)

            self.items = list(self._parse_yaml(yl))

    def _parse_yaml(self, yl):
        for yi in yl:
            name = yi.get('name')
            if name:
                yield User(name=name,
                           email=yi.get('email',''),
                           enabled=yi.get('enabled', False))

    def traits_view(self):
        cols = [ObjectColumn(name='name', editable=False, width=100),
                ObjectColumn(name='email', editable=False, width=200),
                CheckboxColumn(name='enabled')]

        v = View(UItem('items', editor=TableEditor(columns=cols)),
                 title='Select Users to Email',
                 handler=EmailSelectionViewHandler(),
                 buttons=['OK', 'Cancel'],
                 resizable=True)
        return v


if __name__ == '__main__':
    emails = {'Jake': 'foo@nmt.edu', 'Zimmerer': 'bar@nmt.edu', 'root': 'bag@nmt.edu'}
    esv = EmailSelectionView(path='/Users/ross/Pychrondata_dev/setupfiles/users.yaml',
                             emails=emails)
    esv.configure_traits()
# ============= EOF =============================================



