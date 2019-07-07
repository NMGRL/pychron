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
import os
import shutil

from traits.api import HasTraits, Float, Str, List, Bool, Property, Int
from traitsui.api import View, UItem, Item, HGroup, ListEditor, EnumEditor, Label, InstanceEditor, VGroup

from pychron.core.helpers.traitsui_shortcuts import okcancel_view
from pychron.core.pychron_traits import BorderVGroup, StepStr
from pychron.core.utils import alpha_to_int
from pychron.dvc import NPATH_MODIFIERS, analysis_path, dvc_load, dvc_dump
from pychron.experiment.utilities.identifier import make_runid
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

    aliquot = Int
    step = StepStr

    @property
    def icfactor_message(self):
        return [ic.tostr() for ic in self.ic_factors if ic.enabled]

    def traits_view(self):
        icgrp = BorderVGroup(UItem('ic_factors',
                                   editor=ListEditor(mutable=False,
                                                     style='custom',
                                                     editor=InstanceEditor())),
                             label='IC Factors')

        runid_grp = BorderVGroup(HGroup(Item('aliquot'), Item('step')),
                                 label='RunID')

        v = okcancel_view(VGroup(icgrp, runid_grp),
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

        icfs = [ic_factor for ic_factor in self.options.ic_factors if ic_factor.enabled]
        if icfs:
            for ai in ans:
                self._bulk_ic_factor(ai, icfs)

            self.dvc.update_analyses(ans, 'icfactors', '<ICFactor> bulk edit {}'.format(self.options.icfactor_message))

        if self.options.aliquot or self.options.step:
            paths = {}
            for ai in ans:
                expid, ps = self._bulk_runid(ai, self.options.aliquot, self.options.step)
                if expid in paths:
                    pp = paths[expid]
                    pp.extend(ps)
                else:
                    pp = ps

                paths[expid] = pp

            for expid, ps in paths.items():
                if self.dvc.repository_add_paths(expid, ps):
                    self.dvc.repository_commit(expid, '<EDIT> RunID')

    def _bulk_runid(self, ai, aliquot, step):
        if not aliquot:
            aliquot = ai.aliquot
        if not step:
            step = ai.step

        self.dvc.db.modify_aliquot_step(ai.uuid, aliquot, alpha_to_int(step))

        def modify_meta(p):
            jd = dvc_load(p)

            jd['aliquot'] = aliquot
            jd['increment'] = alpha_to_int(step)

            dvc_dump(jd, p)

        ps = []
        repo_id = ai.repository_identifier
        sp = analysis_path(('', ai.record_id), repo_id)
        if sp:
            modify_meta(sp)
            ps.append(sp)
            # using runid path name
            new_runid = make_runid(ai.identifier, aliquot, step)
            for m in NPATH_MODIFIERS:
                sp = analysis_path(('', ai.record_id), repo_id, modifier=m)
                dp = analysis_path(('', new_runid), repo_id, modifier=m, mode='w')
                if sp and os.path.isfile(sp):
                    if os.path.isfile(dp) and m != 'extraction':
                        continue
                    ps.append(sp)
                    ps.append(dp)
                    shutil.move(sp, dp)
        else:
            # using uuid path name
            # only need to modify metadata file
            sp = analysis_path(ai, repo_id)
            modify_meta(sp, aliquot, step)
            ps.append(sp)

        return repo_id, ps

    def _bulk_ic_factor(self, ai, icfs):
        keys, fits = [], []
        for ic_factor in icfs:
            keys.append(ic_factor.det)
            fits.append('bulk_edit')

            # print('ic', ic_factor.det, ic_factor.value, ic_factor.error)
            ic = ai.set_temporary_ic_factor(ic_factor.det, ic_factor.value, ic_factor.error,
                                            tag='{} IC'.format(ic_factor.det))
            for iso in ai.get_isotopes_for_detector(ic_factor.det):
                iso.ic_factor = ic

        ai.dump_icfactors(keys, fits, reviewed=True)


if __name__ == '__main__':
    b = BulkOptions()
    b.detectors = ['H1', 'AX', 'CDD']
    b.configure_traits()
# ============= EOF =============================================
