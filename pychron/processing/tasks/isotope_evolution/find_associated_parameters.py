# ===============================================================================
# Copyright 2014 Jake Ross
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
from datetime import timedelta, datetime

from pychron.core.ui import set_qt


set_qt()

# ============= enthought library imports =======================
from traits.api import HasTraits, Instance, Date, Float, List, Property, Either, Time
from traitsui.api import View, Item, UItem, CheckListEditor, HGroup, VGroup
from traitsui.handler import Controller
import apptools.sweet_pickle as pickle
# ============= standard library imports ========================
import os
# ============= local library imports  ==========================
from pychron.paths import paths


class FindAssociatedParametersModel(HasTraits):
    nominal_hpost_date = Date
    nominal_hpost_time = Time

    nominal_lpost_date = Date
    nominal_lpost_time = Time

    lpost_pad = Float(6)
    hpost_pad = Float(6)

    hpost_date = Property(Date, depends_on='hpost_pad, nominal_hpost_date')
    hpost_time = Property(Time, depends_on='hpost_pad, nominal_hpost_time')

    lpost_date = Property(Date, depends_on='lpost_pad, nominal_lpost_date')
    lpost_time = Property(Time, depends_on='lpost_pad, nominal_lpost_time')

    _hpost_date = Either(Date, None)
    _hpost_time = Either(Time, None)
    _lpost_date = Either(Date, None)
    _lpost_time = Either(Time, None)

    atypes = List
    available_atypes = List(['Blank Air', 'Blank Cocktail', 'Blank Unknown', 'Air', 'Cocktail'])

    mass_spectrometers = List
    available_mass_spectrometers = List

    def get_posts(self):
        return datetime.combine(self.lpost_date, self.lpost_time), \
               datetime.combine(self.hpost_date, self.hpost_time)

    def get_atypes(self):
        return zip(self.atypes, map(lambda x: x.lower().replace(' ', '_'), self.atypes))

    def get_mass_spectrometers(self):
        return map(str.lower, self.mass_spectrometers)

    #hpost
    def _hpost_pad_changed(self):
        self._hpost_date = None
        self._hpost_time = None

    def _get_hpost_time(self):
        if self._hpost_time:
            return self._hpost_time
        else:
            return datetime.combine(self.nominal_hpost_date, self.nominal_hpost_time) + timedelta(hours=self.hpost_pad)

    def _set_hpost_time(self, v):
        self._hpost_time = v

    def _get_hpost_date(self):
        if self._hpost_date:
            return self._hpost_date
        else:
            return self.nominal_hpost_date + timedelta(hours=self.hpost_pad)

    def _set_hpost_date(self, v):
        self._hpost_date = v

    #lpost
    def _lpost_pad_changed(self):
        self._lpost_date = None
        self._lpost_time = None

    def _get_lpost_date(self):
        if self._lpost_date:
            return self._lpost_date
        else:
            return self.nominal_lpost_date - timedelta(hours=self.lpost_pad)

    def _set_lpost_date(self, v):
        self._lpost_date = v

    def _get_lpost_time(self):
        if self._lpost_time:
            return self._lpost_time
        else:
            return datetime.combine(self.nominal_lpost_date, self.nominal_lpost_time) - timedelta(hours=self.lpost_pad)

    def _set_lpost_time(self, v):
        self._lpost_time = v


class FindAssociatedParametersDialog(Controller):
    model = Instance(FindAssociatedParametersModel)

    def __init__(self, *args, **kw):
        super(FindAssociatedParametersDialog, self).__init__(*args, **kw)
        p = os.path.join(paths.hidden_dir, 'find_associated_parameters_dialog')
        if os.path.isfile(p):
            with open(p, 'r') as fp:
                try:
                    self.model = pickle.load(fp)
                except (pickle.PickleError, AttributeError, OSError, EOFError):
                    pass
        if not self.model:
            self.model = FindAssociatedParametersModel()

    def closed(self, info, is_ok):
        if is_ok:
            p = os.path.join(paths.hidden_dir, 'find_associated_parameters_dialog')
            with open(p, 'w') as fp:
                try:
                    pickle.dump(self.model, fp)
                except pickle.PickleError:
                    pass

    def traits_view(self):
        hgrp = VGroup(HGroup(Item('hpost_pad', label='Pad')),
                      UItem('hpost_date', style='custom'),
                      HGroup(UItem('hpost_time')),
                      show_border=True,
                      label='High')

        lgrp = VGroup(HGroup(Item('lpost_pad', label='Pad')),
                      UItem('lpost_date', style='custom'),
                      HGroup(UItem('lpost_time')),
                      show_border=True,
                      label='Low')
        atype_grp = HGroup(UItem('atypes',
                                 style='custom',
                                 editor=CheckListEditor(name='available_atypes', cols=3)),
                           show_border=True, label='Analysis Types')

        mgrp = HGroup(UItem('mass_spectrometers',
                            style='custom',
                            editor=CheckListEditor(name='available_mass_spectrometers', cols=3)),
                      show_border=True, label='Mass Spectrometers')

        v = View(VGroup(HGroup(lgrp, hgrp),
                        atype_grp,
                        mgrp),
                 title='Find Associated Parameters',
                 buttons=['OK', 'Cancel'])
        return v


if __name__ == '__main__':
    f = FindAssociatedParametersDialog()

    today = datetime.today()
    # f.model.nominal_lpost_date=today.date()
    f.model.nominal_lpost_date = today.date()
    f.model.nominal_lpost_time = today.time()

    f.model.nominal_hpost_date = today.date()
    f.model.nominal_hpost_time = today.time()

    f.model.available_mass_spectrometers = ['Jan', 'Obama']
    f.configure_traits()

    print f.model.get_atypes()
    found = []
    for n, a in f.model.get_atypes():
        found.append((n, 4))
    m = '\n'.join(['{:<20s} = {}'.format(*fi) for fi in found])
    msg = 'Found Associated Analyses\n{}'.format(m)
    print msg
    print f.model.get_posts()
    print f.model.get_mass_spectrometers()
# ============= EOF =============================================

