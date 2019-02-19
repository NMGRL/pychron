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

from __future__ import absolute_import

from reportlab.lib.pagesizes import A4, letter, landscape, A2, A0
from reportlab.lib.units import inch, cm
from traits.api import Str, Bool, Enum, Button, Float, Color
from traitsui.api import View, Item, UItem, HGroup, Group, VGroup, spring, Spring

from pychron.core.helpers.traitsui_shortcuts import okcancel_view
from pychron.core.pdf.pdf_graphics_context import UNITS_MAP
from pychron.core.persistence_options import BasePersistenceOptions
from pychron.envisage.icon_button_editor import icon_button_editor
from pychron.persistence_loggable import dumpable
from pychron.pychron_constants import SIG_FIGS

PAGE_MAP = {'A4': A4, 'letter': letter, 'A2': A2, 'A0': A0}
UNITS_MAP = {'inch': inch, 'cm': cm}
COLUMN_MAP = {'1': 1, '2': 0.5, '3': 0.33, '2/3': 0.66}

mgrp = VGroup(HGroup(Spring(springy=False, width=100),
                     Item('top_margin', label='Top'),
                     spring, ),
              HGroup(Item('left_margin', label='Left'),
                     Item('right_margin', label='Right')),
              HGroup(Spring(springy=False, width=100), Item('bottom_margin', label='Bottom'),
                     spring),
              label='Margins', show_border=True)
cgrp = VGroup()

sgrp = VGroup(Item('page_type'),
              Item('fit_to_page'),
              HGroup(Item('use_column_width', enabled_when='not fit_to_page'),
                     Item('columns', enabled_when='use_column_width')),
              HGroup(Item('fixed_width', label='W', enabled_when='not use_column_width and not fit_to_page or '
                                                                 'page_type=="custom"'),
                     Item('fixed_height', label='H', enabled_when='not fit_to_page or page_type=="custom"'),
                     Item('units', enabled_when='not fit_to_page or page_type=="custom"')),

              label='Size', show_border=True)

PDFLayoutGroup = VGroup(Item('orientation'),
                        mgrp,
                        sgrp,
                        cgrp,
                        label='Layout')

PDFLayoutView = okcancel_view(PDFLayoutGroup,
                              title='PDF Save Options')


class BasePDFOptions(BasePersistenceOptions):
    orientation = dumpable(Enum('landscape', 'portrait'))
    left_margin = dumpable(Float(1.5))
    right_margin = dumpable(Float(1))
    top_margin = dumpable(Float(1))
    bottom_margin = dumpable(Float(1))
    show_page_numbers = dumpable(Bool(False))

    _persistence_name = 'base_pdf_options'

    page_number_format = None
    fixed_width = dumpable(Float)
    fixed_height = dumpable(Float)

    page_type = dumpable(Enum('letter', 'A4', 'A2', 'A0', 'custom'))
    units = dumpable(Enum('inch', 'cm'))
    use_column_width = dumpable(Bool(True))
    columns = dumpable(Enum('1', '2', '3', '2/3'))
    fit_to_page = dumpable(Bool)

    @property
    def bounds(self):
        units = UNITS_MAP[self.units]
        if self.page_type == 'custom':
            page = [self.fixed_width * units, self.fixed_height * units]
        else:
            page = PAGE_MAP[self.page_type]

        if self.fit_to_page:
            if self.orientation == 'landscape':
                b = [page[1], page[0]]
            else:
                b = [page[0], page[1]]

            b[0] -= (self.left_margin + self.right_margin) * units
            b[1] -= (self.top_margin + self.bottom_margin) * units

        elif self.use_column_width:
            if self.orientation == 'landscape':
                page = landscape(page)
                width_margins = self.bottom_margin + self.top_margin
            else:
                width_margins = self.left_margin + self.right_margin
            fw = page[0]
            w = fw - width_margins * units
            # print 'cw', w, fw, width_margins, width_margins * units, COLUMN_MAP[self.columns]
            nw = w * COLUMN_MAP[self.columns]
            b = [nw, nw]
        else:
            b = [self.fixed_width * units, self.fixed_height * units]

        return b

    @property
    def page_size(self):
        if self.page_type == 'custom':
            units = UNITS_MAP[self.units]
            ps = self.fixed_width * units, self.fixed_height * units
        else:
            orientation = 'landscape_' if self.orientation == 'landscape' else ''
            ps = '{}{}'.format(orientation, self.page_type)
        return ps

    @property
    def dest_box(self):
        units = UNITS_MAP[self.units]
        w, h = self.bounds
        w /= units
        h /= units
        return self.left_margin, self.bottom_margin, w, h

    def _get_layout_group(self):
        return PDFLayoutGroup


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
    kca_sig_figs = Enum(*SIG_FIGS)
    age_sig_figs = Enum(*SIG_FIGS)

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

        v = okcancel_view(layout_grp,
                          table_grp,
                          data_grp,
                          title='PDF Options',
                          buttons=['OK', 'Cancel', 'Revert'])
        return v

# ============= EOF =============================================
