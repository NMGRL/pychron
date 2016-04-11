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
import os
import pickle

from datetime import datetime, timedelta
from pyface.tasks.task_layout import PaneItem
from traits.has_traits import HasTraits
from traits.trait_types import Float, Date, Time
from traits.traits import Property
from traitsui.group import HGroup, VGroup
from traitsui.item import UItem
from traitsui.view import View

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.paths import paths


def browser_pane_item(width=300):
    return PaneItem('pychron.browser', width=width)


# ===============================================================
def get_pad(low, high):
    p=os.path.join(paths.hidden_dir, 'pad_entry.p')
    pe =None
    if os.path.isfile(p):
        try:
            with open(p, 'r') as rfile:
                pe = pickle.load(rfile)
        except (pickle.PickleError, OSError, EOFError):
            pass

    if not pe:
        pe=PadEntry()

    pe.trait_set(**{'low_post':low,
                    'high_post':high,
                    'olow_post':low,
                    'ohigh_post':high,
                    })
    pe.update_pad()

    info=pe.edit_traits()
    if info.result:
        with open(p, 'w') as wfile:
            pickle.dump(pe, wfile)
        return pe


class PadEntry(HasTraits):
    pad = Float
    olow_post=Date
    ohigh_post=Date

    low_post = Property(depends_on='low_post_data, low_post_time')
    low_post_date=Date
    low_post_time=Time
    
    high_post = Property(depends_on='high_post_data, high_post_time')
    high_post_date=Date
    high_post_time=Time

    def update_pad(self):
        self._pad_changed(self.pad)

    def _pad_changed(self, pad):
        if self.olow_post and self.ohigh_post:
            td=timedelta(hours=pad)
            lp,hp=self.olow_post,self.ohigh_post

            lp-=td
            hp+=td

            self.low_post, self.high_post=lp,hp

    def _set_high_post(self, v):
        self.high_post_date=v.date()
        self.high_post_time=v.time()

    def _set_low_post(self, v):
        self.low_post_date=v.date()
        self.low_post_time=v.time()

    def _get_high_post(self):
        return datetime.combine(self.high_post_date, self.high_post_time)

    def _get_low_post(self):
        return datetime.combine(self.low_post_date, self.low_post_time)

    def traits_view(self):
        l=VGroup(UItem('low_post_time'),
                 UItem('low_post_date', style='custom'))
        h=VGroup(UItem('high_post_time'),
                 UItem('high_post_date', style='custom'))

        v=View(UItem('pad'),
               HGroup(l,h),
               kind='livemodal',
               width=500,
               resizable=True,
               buttons=['OK','Cancel'])
        return v

# ============= EOF =============================================



