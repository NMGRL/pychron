# ===============================================================================
# Copyright 2013 Jake Ross
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
from pyface.action.menu_manager import MenuManager
from traits.api import Int, Property
from traitsui.menu import Action
from traitsui.tabular_adapter import TabularAdapter
from uncertainties import nominal_value, std_dev

from pychron.core.helpers.color_generators import colornames
from pychron.core.helpers.formatting import floatfmt
from pychron.database.records.isotope_record import IsotopeRecordView

# ============= standard library imports ========================
# ============= local library imports  ==========================


class UnknownsAdapter(TabularAdapter):
    columns = [('Run ID', 'record_id'),
               # ('Class','klass'),
               ('Sample', 'sample'),
               ('Age', 'age'),
               (u'\u00b11\u03c3', 'error'),
               ('Tag', 'tag'),
               ('GID', 'graph_id')]

    record_id_width = Int(80)
    sample_width = Int(80)
    age_width = Int(70)
    error_width = Int(60)
    tag_width = Int(50)
    graph_id_width = Int(30)

    font = 'arial 10'
    #     record_id_text_color = Property
    #     tag_text_color = Property
    age_text = Property
    error_text = Property

    # klass_text = Property
    # def _get_klass_text(self):
    #     return self.item.__class__.__name__.split('.')[-1]

    def get_menu(self, object, trait, row, column):
        return MenuManager(Action(name='Group Selected', action='group_by_selected'),
                           Action(name='Group by Labnumber', action='group_by_labnumber'),
                           Action(name='Group by Aliquot', action='group_by_aliquot'),
                           Action(name='Clear Grouping', action='clear_grouping'),
                           Action(name='Unselect', action='unselect'))

    def get_bg_color(self, obj, trait, row, column=0):
        c = 'white'
        if not isinstance(self.item, IsotopeRecordView):
            if self.item.tag == 'invalid':
                c = '#C9C5C5'
            elif self.item.is_omitted():
                c = '#FAC0C0'
        return c

    def _get_age_text(self):
        r = ''
        if not isinstance(self.item, IsotopeRecordView):
            r = floatfmt(nominal_value(self.item.uage), n=3)
        return r

    def _get_error_text(self):
        r = ''
        if not isinstance(self.item, IsotopeRecordView):
            r = floatfmt(std_dev(self.item.uage_wo_j_err), n=4)
        return r

    def get_text_color(self, obj, trait, row, column=0):
        n = len(colornames)
        gid = obj.items[row].group_id
        cid = gid % n

        return colornames[cid]


class ReferencesAdapter(TabularAdapter):
    columns = [
        ('Run ID', 'record_id'), ]
    font = 'arial 10'

# ============= EOF =============================================
