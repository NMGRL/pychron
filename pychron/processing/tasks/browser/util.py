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

from traits.has_traits import HasTraits
from traits.trait_types import Float
from traitsui.item import UItem
from traitsui.view import View
from pyface.tasks.task_layout import PaneItem

#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.paths import paths


def browser_pane_item(width=300):
    return PaneItem('pychron.browser', width=width)


def get_pad():
    p=os.path.join(paths.hidden_dir, 'pad_entry')
    pe =None
    if os.path.isfile(p):
        try:
            with open(p, 'r') as fp:
                pe = pickle.load(fp)
        except (pickle.PickleError, OSError, EOFError):
            pass

    if not pe:
        pe=PadEntry()

    info=pe.edit_traits()
    if info.result:
        with open(p, 'w') as fp:
            pickle.dump(pe, fp)
        return pe.pad

class PadEntry(HasTraits):
    pad = Float
    def traits_view(self):
        v=View(UItem('pad'),
               kind='livemodal',
               width=300,
               buttons=['OK','Cancel'])
        return v

#============= EOF =============================================



