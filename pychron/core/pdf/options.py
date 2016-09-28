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
import os

from traits.api import Str, Bool, Enum, Button, Float, Int, Color
from traitsui.api import View, Item, UItem, HGroup, Group, VGroup

from pychron.core.persistence_options import BasePersistenceOptions
from pychron.envisage.icon_button_editor import icon_button_editor
from pychron.paths import paths
from pychron.persistence_loggable import dumpable


class BasePDFOptions(BasePersistenceOptions):
    orientation = dumpable(Enum('landscape', 'portrait'))
    left_margin = dumpable(Float(1.5))
    right_margin = dumpable(Float(1))
    top_margin = dumpable(Float(1))
    bottom_margin = dumpable(Float(1))
    show_page_numbers = dumpable(Bool(False))

    _persistence_name = 'base_pdf_options'

    page_number_format = None

    def __init__(self, *args, **kw):
        self.persistence_path = os.path.join(paths.hidden_dir, self._persistence_name)

    def _get_layout_group(self):
        margin_grp = VGroup(Item('left_margin', label='Left (in.)'),
                           Item('right_margin', label='Right (in.)'),
                           Item('top_margin', label='Top (in.)'),
                           Item('bottom_margin', label='Bottom (in.)'),
                            show_border=True, label='Margins')

        layout_grp = Group(Item('orientation'),
                           margin_grp,
                           Item('show_page_numbers', label='Page Numbers'),
                           show_border=True,
                           label='layout')
        return layout_grp


class PDFTableOptions(BasePDFOptions):
    title = Str
    auto_title = Bool

    use_alternating_background = Bool
    alternating_background = Color

    default_row_height = Float(0.22)
    default_header_height = Float(0.22)
    options_button = Button
    age_nsigma = Enum(1, 2, 3)
    kca_nsigma = Enum(1, 2, 3)
    link_sigmas = Bool(True)

    age_units = Enum('Ma', 'ka', 'Ga', 'a')
    kca_sig_figs = Int
    age_sig_figs = Int

    _persistence_name = 'table_pdf_options'

    def _load_yaml_hook(self, d):

        self.age_nsigma = d.get('age_nsigma', 2)
        self.kca_nsigma = d.get('kca_nsigma', 2)
        self.link_sigmas = d.get('link_sigmas', True)

        self.age_sig_figs = d.get('age_sig_figs', 3)

        self.kca_sig_figs = d.get('kca_sig_figs', 3)

        self.age_units = d.get('age_units', 'Ma')

    def _get_dump_attrs(self):
        return ('auto_title',
                'age_nsigma',
                'kca_nsigma',
                'link_sigmas',
                'age_sig_figs',
                'kca_sig_figs',
                'age_units')

    def get_dump_dict(self):
        d = super(PDFTableOptions, self).get_dump_dict()
        d.update(dict(title=str(self.title)))

        return d

    def _options_button_fired(self):
        if self.edit_traits(view='advanced_view', kind='livemodal'):
            self.dump_yaml()

    def _age_nsigma_changed(self):
        if self.link_sigmas:
            self.kca_nsigma = self.age_nsigma

    def _kca_nsigma_changed(self):
        if self.link_sigmas:
            self.age_nsigma = self.kca_nsigma

    def _link_sigmas_changed(self):
        if self.link_sigmas:
            self.kca_nsigma = self.age_nsigma

    def traits_view(self):
        v = View(HGroup(Item('auto_title'),
                        UItem('title', enabled_when='not auto_title'),
                        icon_button_editor('options_button', 'cog')))
        return v

    def advanced_view(self):
        table_grp = Group(Item('use_alternating_background'),
                          Item('alternating_background'),
                          label='Table')

        layout_grp = self._get_layout_grp()

        data_grp = Group(Item('link_sigmas', label='Link'),
                         Item('age_nsigma', label='Age NSigma'),
                         Item('kca_nsigma', label='K/CA NSigma'),
                         Item('age_units'),
                         VGroup(
                             HGroup(Item('age_sig_figs', label='Age')),
                             HGroup(Item('kca_sig_figs', label='K/Ca')),
                             label='Sig Figs'),
                         label='Data')
        v = View(
            layout_grp,
            table_grp,
            data_grp,
            title='PDF Options',
            buttons=['OK', 'Cancel', 'Revert'])
        return v

# ============= EOF =============================================
