# ===============================================================================
# Copyright 2020 ross
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
import json
import os

from traits.api import List, Instance, Str, Float, HasTraits, Button, Int, Bool
from traitsui.api import UItem, TableEditor, HGroup, VGroup
from traitsui.extras.checkbox_column import CheckboxColumn
from traitsui.table_column import ObjectColumn

from pychron.core.helpers.traitsui_shortcuts import okcancel_view
from pychron.envisage.icon_button_editor import icon_button_editor
from pychron.loggable import Loggable
from pychron.paths import paths


class CorrelationEllipse(HasTraits):
    name = Str
    age_min = Float
    age_max = Float
    kca_min = Float
    kca_max = Float
    active = Bool(True)

    @classmethod
    def duplicate(cls, obj):
        return cls(name=obj.name,
                   age_min=obj.age_min,
                   age_max=obj.age_max,
                   kca_min=obj.kca_min,
                   kca_max=obj.kca_max,
                   active=obj.active)

    def tojson(self):
        return {'age': {'min': self.age_min, 'max': self.age_max},
                'kca': {'min': self.kca_min, 'max': self.kca_max},
                'active': self.active}


class CorrelationEllipsesEditor(Loggable):
    dvc = Instance('pychron.dvc.dvc.DVC')
    items = List

    add_row_button = Button
    delete_row_button = Button
    duplicate_row_button = Button

    selected_row = Int

    @property
    def persistence_path(self):
        return os.path.join(paths.meta_root, 'correlation_ellipses.json')

    def dump(self):
        self.dvc.meta_pull()
        with open(self.persistence_path, 'w') as wfile:
            obj = {i.name: i.tojson() for i in self.items}
            json.dump(obj, wfile, indent=2)

        # add, commit, push
        if self.dvc.meta_repo.add_paths(self.persistence_path):
            self.dvc.meta_commit('Updated correlation ellipses')
            self.dvc.meta_push()

    def load(self):
        self.dvc.meta_pull()

        def factory(k, v):
            return CorrelationEllipse(name=k,
                                      active=v.get('active', True),
                                      age_min=v['age']['min'],
                                      age_max=v['age']['max'],
                                      kca_min=v['kca']['min'],
                                      kca_max=v['kca']['max'])

        if os.path.isfile(self.persistence_path):
            with open(self.persistence_path, 'r') as rfile:
                jd = json.load(rfile)
                self.items = [factory(k, ji) for k, ji in jd.items()]

    def _add_row_button_fired(self):
        item = CorrelationEllipse(name=str(len(self.items)))
        self.items.append(item)

    def _delete_row_button_fired(self):
        if self.selected_row is not None:
            self.items.pop(self.selected_row)

    def _duplicate_row_button_fired(self):
        if self.selected_row is not None:
            item = self.items[self.selected_row]

            nitem = CorrelationEllipse.duplicate(item)
            self.items.append(nitem)

    def traits_view(self):
        cols = [CheckboxColumn(name='active'),
                ObjectColumn(name='name'),
                ObjectColumn(name='kca_min'),
                ObjectColumn(name='kca_max'),
                ObjectColumn(name='age_min'),
                ObjectColumn(name='age_max'),
                ]

        button_grp = HGroup(icon_button_editor('add_row_button', 'add', tooltip='Add row'),
                            icon_button_editor('delete_row_button', 'delete', tooltip='Delete selected rows'),
                            icon_button_editor('duplicate_row_button', 'duplicate', tooltip='Duplicate selected rows'))

        return okcancel_view(VGroup(button_grp,
                                    UItem('items',
                                          editor=TableEditor(columns=cols,
                                                             selected_indices='selected_row'))),
                             title='Edit Correlation Ellipses',
                             width=550, height=700)


if __name__ == '__main__':
    c = CorrelationEllipsesEditor()
    c.configure_traits()
# ============= EOF =============================================
