#===============================================================================
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
#===============================================================================

#============= enthought library imports =======================

from traits.api import HasTraits, on_trait_change, Instance, List, Event, Any, Enum, Button, Float
from traitsui.api import View, Item, Controller, UItem
#============= standard library imports ========================
#============= local library imports  ==========================
from uncertainties import ufloat
from pychron.core.ui.progress_dialog import myProgressDialog


class K3739EditModel(HasTraits):
    analyses = List
    k3739 = Float
    k3739_err = Float
    progress = Any

    def apply_modified(self):
        v = ufloat(self.k3739, self.k3739_err)

        ans = self.analyses
        pd = myProgressDialog(max=len(ans) - 1)
        pd.open()

        for ai in ans:
            pd.change_message('Modifying k3739 for {}'.format(ai.record_id))
            ai.interference_corrections['k3739'] = v
            ai.calculate_age(force=True)
        pd.close()


class K3739EditView(Controller):
    model = K3739EditModel

    def closed(self, info, is_ok):
        if is_ok:
            self.model.apply_modified()

    def traits_view(self):
        v = View(Item('k3739', label='(37/39)K'),
                 UItem('k3739_err'),
                 title='Edit (37/39)K',
                 buttons=['OK', 'Cancel'],
                 kind='livemodal')
        return v

#============= EOF =============================================

