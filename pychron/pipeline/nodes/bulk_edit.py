# ===============================================================================
# Copyright 2018 ross
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
from traits.api import HasTraits, Float, Str, List, Bool, Property
from traitsui.api import View, UItem, Item, HGroup, ListEditor, EnumEditor, Label, InstanceEditor

from pychron.core.helpers.traitsui_shortcuts import okcancel_view
from pychron.pipeline.nodes.data import BaseDVCNode
from pychron.pychron_constants import PLUSMINUS


class ICFactor(HasTraits):
    det = Str
    detectors = List
    value = Float
    error = Float
    use = Bool
    enabled = Property

    def _get_enabled(self):
        return self.use and self.det and self.value

    def traits_view(self):
        v = View(HGroup(UItem('use'),
                        UItem('det', editor=EnumEditor(name='detectors')),
                        Item('value'),
                        Label(PLUSMINUS),
                        UItem('error')))
        return v

    def tostr(self):
        return '{}:{}({})'.format(self.det, self.value, self.error)


class BulkOptions(HasTraits):
    ic_factors = List
    detectors = List

    @property
    def icfactor_message(self):
        return [ic.tostr() for ic in self.ic_factors if ic.enabled]

    def traits_view(self):
        v = okcancel_view(UItem('ic_factors',
                                editor=ListEditor(mutable=False,
                                                  style='custom',
                                                  editor=InstanceEditor())),
                          title='Bulk Edit Options')
        return v

    def _ic_factors_default(self):
        return [ICFactor(detectors=self.detectors),
                ICFactor(detectors=self.detectors),
                ICFactor(detectors=self.detectors)]


class BulkEditNode(BaseDVCNode):
    options_klass = BulkOptions
    name = 'Bulk Edit'

    def pre_run(self, state, configure=True):
        if state.unknowns:
            dets = list({iso.detector for ai in state.unknowns for iso in ai.itervalues()})
            self.options.detectors = dets

        return super(BulkEditNode, self).pre_run(state, configure=configure)

    def run(self, state):
        ans = state.unknowns

        for ai in ans:
            self._bulk_ic_factor(ai)

        self.dvc.update_analyses(ans, 'icfactors', '<ICFactor> bulk edit {}'.format(self.options.icfactor_message))

    def _bulk_ic_factor(self, ai):
        dump_ic = False
        keys, fits = [], []
        for ic_factor in self.options.ic_factors:
            if ic_factor.enabled:
                keys.append(ic_factor.det)
                fits.append('bulk_edit')

                # print('ic', ic_factor.det, ic_factor.value, ic_factor.error)
                ic = ai.set_temporary_ic_factor(ic_factor.det, ic_factor.value, ic_factor.error,
                                                tag='{} IC'.format(ic_factor.det))
                for iso in ai.get_isotopes_for_detector(ic_factor.det):
                    iso.ic_factor = ic
                dump_ic = True

        if dump_ic:
            ai.dump_icfactors(keys, fits, reviewed=True)


if __name__ == '__main__':
    b = BulkOptions()
    b.detectors = ['H1', 'AX', 'CDD']
    b.configure_traits()
# ============= EOF =============================================
