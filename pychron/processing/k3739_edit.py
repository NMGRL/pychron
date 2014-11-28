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

#============= enthought library imports =======================
import os
import pickle

from traits.api import HasTraits, Bool, List, Any, Float
from traitsui.api import View, Item,UItem, Controller, VGroup, HGroup, TabularEditor


#============= standard library imports ========================
#============= local library imports  ==========================
from uncertainties import ufloat
from pychron.core.ui.progress_dialog import myProgressDialog
from pychron.paths import paths
from pychron.processing.tasks.browser.panes import AnalysisAdapter
from pychron.pychron_constants import PLUSMINUS_SIGMA


class K3739EditModel(HasTraits):
    analyses = List
    k3739 = Float
    k3739_err = Float
    progress = Any
    normal_k3739 = Bool
    save_to_db = Bool

    def __init__(self, *args, **kw):
        super(K3739EditModel, self).__init__(*args, **kw)
        self.load()

    def apply_modified(self):
        if self.normal_k3739:
            v = None
        else:
            v = ufloat(self.k3739, self.k3739_err)
        ans = self.analyses
        pd = myProgressDialog(max=len(ans) - 1)
        pd.open()

        for ai in ans:
            pd.change_message('Modifying k3739 for {}'.format(ai.record_id))
            ai.fixed_k3739 = v
            ai.calculate_age(force=True)
        pd.close()

        self.dump()

    #persistence
    def load(self):
        p = self.pickle_path
        if os.path.isfile(p):
            try:
                with open(p, 'rb') as fp:
                    d = pickle.load(fp)
                    self.trait_set(**d)
            except BaseException:
                pass

    def dump(self):
        d = dict(k3739=self.k3739, k3739_err=self.k3739_err)
        try:
            with open(self.pickle_path, 'wb') as fp:
                pickle.dump(d, fp)
        except BaseException:
            pass

    @property
    def pickle_path(self):
        return os.path.join(paths.hidden_dir, 'modified_k3739')

    @property
    def value_str(self):
        if self.normal_k3739:
            return 'normal'
        else:
            return 'fixed ({}+/-{})'.format(self.k3739, self.k3739_err)


class K3739EditView(Controller):
    model = K3739EditModel

    # def closed(self, info, is_ok):
    #     if is_ok:
    #         self.model.apply_modified()

    def traits_view(self):
        v = View(
            VGroup(
                Item('normal_k3739', label='Normal (37/39)K'),
                HGroup(
                    Item('k3739', label='(37/39)K'),
                    Item('k3739_err', label=PLUSMINUS_SIGMA),
                    show_border=True,
                    enabled_when='not normal_k3739')),
            UItem('analyses', editor=TabularEditor(adapter=AnalysisAdapter())),
            HGroup(Item('save_to_db', label='Save to Database')),
            title='Edit (37/39)K',
            buttons=['OK', 'Cancel'],
            kind='livemodal')
        return v

# ============= EOF =============================================

