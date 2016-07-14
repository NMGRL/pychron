# ===============================================================================
# Copyright 2015 Jake Ross
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

from traits.api import Str, Int, Bool, List
from traitsui.api import View, VGroup, Item, EnumEditor, HGroup

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.paths import paths
from pychron.persistence_loggable import PersistenceLoggable


class AutoGenConfig(PersistenceLoggable):
    start_blank = Bool(True)
    end_blank = Bool
    start_air = Bool
    end_air = Bool

    start_cocktail = Bool
    end_cocktail = Bool

    blank_freq = Int(3)
    air_freq = Int
    cocktail_freq = Int
    run_block_freq = Int

    run_block = Str
    run_blocks = List

    end_run_block = Str
    start_run_block = Str

    pattributes = ('start_blank',
                   'start_air',
                   'start_cocktail',
                   'start_run_block',

                   'end_blank',
                   'end_air',
                   'end_cocktail',
                   'end_run_block',

                   'blank_freq',
                   'air_freq',
                   'cocktail_freq',
                   'run_block_freq',

                   'run_block',
                   'run_blocks')

    def traits_view(self):
        sgrp = VGroup(Item('start_blank', label='Blank Unknown'),
                      Item('start_air', label='Air'),
                      Item('start_cocktail', label='Cocktail'),
                      label='Start', show_border=True)

        egrp = VGroup(Item('end_blank', label='Blank Unknown'),
                      Item('end_air', label='Air'),
                      Item('end_cocktail', label='Cocktail'),
                      label='End', show_border=True)
        fgrp = VGroup(Item('blank_freq', label='Blank Unknown'),
                      Item('air_freq', label='Air'),
                      Item('cocktail_freq', label='Cocktail'),
                      HGroup(Item('run_block',
                                  label='Run Block',
                                  editor=EnumEditor(name='run_blocks')),
                             Item('run_block_freq')),
                      label='Frequency', show_border=True)

        v = View(VGroup(sgrp, fgrp, egrp),
                 title='Edit Quene Generation Configuration',
                 buttons=['OK', 'Cancel'],
                 kind='livemodal')
        return v

    @property
    def persistence_path(self):
        return os.path.join(paths.hidden_dir, 'auto_gen_config.p')

# ============= EOF =============================================



