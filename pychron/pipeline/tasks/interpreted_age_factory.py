# ===============================================================================
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
# ===============================================================================

# ============= enthought library imports =======================
from pyface.confirmation_dialog import confirm
from pyface.constant import YES
from pyface.message_dialog import information
from traits.api import List, HasTraits, Button, Any
from traitsui.api import View, Item, TableEditor, EnumEditor, Controller, VGroup, TextEditor, HGroup, UItem
from traitsui.extras.checkbox_column import CheckboxColumn
from traitsui.table_column import ObjectColumn

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.core.helpers.iterfuncs import groupby_key
from pychron.core.helpers.traitsui_shortcuts import okcancel_view
from pychron.entry.providers.macrostrat import get_lithology_values
from pychron.envisage.icon_button_editor import icon_button_editor
from pychron.processing.analyses.analysis_group import InterpretedAgeGroup
from pychron.processing.analyses.preferred import preferred_item


class BaseColumn(ObjectColumn):
    text_font = 'arial 10'


class UObjectColumn(BaseColumn):
    editable = False


lithology_grp = VGroup(Item('lithology', editor=EnumEditor(name='lithologies')),
                       Item('lithology_class', label='Class', editor=EnumEditor(name='lithology_classes')),
                       Item('lithology_group', label='Group', editor=EnumEditor(name='lithology_groups')),
                       Item('lithology_type', label='Type', editor=EnumEditor(name='lithology_types')),
                       show_border=True, label='Lithology')

metadata_grp = VGroup(HGroup(Item('sample'), Item('igsn')),
                      HGroup(Item('material'), UItem('grainsize', tooltip='Grainsize (optional)')),
                      Item('project'),
                      Item('reference', label='Reference',
                           tooltip='Published reference/citation for this interpreted age'),
                      Item('rlocation', label='Relative Location', tooltip='Relative location of the sample '
                                                                           'within the unit'),
                      HGroup(Item('latitude', label='Lat.'), Item('longitude', label='Lon.')),
                      lithology_grp,
                      show_border=True,
                      label='MetaData')


class TItem(Item):
    def _editor_default(self):
        return TextEditor(read_only=True, format_str='%0.3f')


EDIT_VIEW = View(HGroup(preferred_item,
                        metadata_grp))

cols = [
    CheckboxColumn(name='use', label='Save', width=10),
    UObjectColumn(name='identifier', width=50),
    BaseColumn(name='name', width=50),
    BaseColumn(name='repository_identifier',
               width=50,
               editor=EnumEditor(name='controller.repository_identifiers')),
]

editor = TableEditor(columns=cols, orientation='vertical',
                     sortable=False, edit_view=EDIT_VIEW)

VIEW = okcancel_view(HGroup(icon_button_editor('sync_metadata_button', 'database_link',
                                               tooltip='Sync the Interpreted Age metadata with the database. This '
                                                       'will supersede the metadata saved with the analyses. Use '
                                                       'this option if the metadata is missing or if the metadata '
                                                       'was modified after analysis')),
                     Item('items', show_label=False, editor=editor),
                     width=1200,
                     title='Set Interpreted Age')


class InterpretedAgeFactoryModel(HasTraits):
    items = List
    sync_metadata_button = Button
    dvc = Any

    def _sync_metadata_button_fired(self):
        with self.dvc.session_ctx():
            for it in self.items:
                self.dvc.sync_ia_metadata(it)

        information(None, 'Metadata sync complete')


class InterpretedAgeFactoryView(Controller):
    repository_identifiers = List
    traits_view = VIEW


def set_interpreted_age(dvc, ias):
    repos = dvc.get_local_repositories()
    liths, groups, classes, types = get_lithology_values()
    for ia in ias:
        ia.lithology_classes = classes
        ia.lithology_groups = groups
        ia.lithology_types = types
        ia.lithologies = liths

    model = InterpretedAgeFactoryModel(items=ias,
                                       dvc=dvc)
    iaf = InterpretedAgeFactoryView(model=model,
                                    repository_identifiers=repos)

    while 1:
        info = iaf.edit_traits()
        if info.result:
            no_lat_lon = []
            ias = [ia for ia in ias if ia.use]
            for ia in ias:
                if not ia.latitude and not ia.longitude:
                    no_lat_lon.append('{} ({})'.format(ia.name, ia.identifier))

            if no_lat_lon:
                n = ','.join(no_lat_lon)
                if not confirm(None, 'No Lat/Lon. entered for {}. Are you sure you want to continue without setting a '
                                     'Lat/Lon?'.format(n)) == YES:
                    continue

            ris = []
            for rid, iass in groupby_key(ias, key='repository_identifier'):
                if dvc.add_interpreted_ages(rid, iass):
                    ris.append(rid)

            if ris:
                if confirm(None, 'Would you like to share changes to {}?'.format(','.join(ris))) == YES:
                    for rid in ris:
                        dvc.push_repository(rid)
                    information(None, 'Pushes complete')

            break
        else:
            break


if __name__ == '__main__':
    m = InterpretedAgeFactoryModel()
    m.items = [InterpretedAgeGroup()]
    c = InterpretedAgeFactoryView(model=m)
    c.configure_traits()
# ============= EOF =============================================
