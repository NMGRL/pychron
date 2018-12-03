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

from traits.api import Instance, Str, Bool
from traitsui.api import View, UItem, Item, VGroup

from pychron.core.helpers.iterfuncs import groupby_repo, groupby_key
from pychron.core.progress import progress_loader
from pychron.dvc import dvc_dump, dvc_load, MASS_SPEC_REDUCED
from pychron.dvc.dvc import DVC
from pychron.mass_spec.mass_spec_recaller import MassSpecRecaller
from pychron.paths import paths
from pychron.pipeline.nodes.base import BaseNode


class MassSpecReducedNode(BaseNode):
    name = 'Mass Spec Reduced'
    recaller = Instance(MassSpecRecaller)
    dvc = Instance(DVC)

    message = Str
    share_changes = Bool

    _paths = None

    def traits_view(self):
        v = View(VGroup(VGroup(UItem('message', style='custom'), label='Message', show_border=True),
                        Item('share_changes', label='Share Changes')),
                 title='Configure Mass Spec Reduced',
                 buttons=['OK', 'Cancel'])
        return v

    def run(self, state):
        if self.recaller.connect():

            self.dvc.create_session()
            for repo, unks in groupby_repo(state.unknowns):

                self.dvc.pull_repository(repo)
                self._paths = []

                # freeze flux
                unks = list(unks)
                self._freeze_flux(repo, unks)
                self._import_reduced(unks)
                self._save(repo)

    def _freeze_flux(self, repo, unks):
        """
        save a flux file called <IRRADNAME>.json

        simple dictionary of identifier: flux_dict

        10000: {
                value: 0.1
                error: 0.001
                }
        :param repo:
        :param unks:
        :return:
        """
        for irrad, unks in groupby_key(unks, 'irradiation'):
            unks = list(unks)
            self._make_flux_file(repo, irrad, unks)
            levels = {u.irradiation_level for u in unks}
            for l in levels:
                self._make_production_file(repo, irrad, l)

    def _make_production_file(self, repo, irrad, level):
        prod = self.recaller.get_production(irrad, level)
        path = os.path.join(paths.repository_dataset_dir, repo, '{}.{}.production.json'.format(irrad, level))
        dvc_dump(prod, path)
        self._paths.append(path)

    def _make_flux_file(self, repo, irrad, unks):
        path = os.path.join(paths.repository_dataset_dir, repo, '{}.json'.format(irrad))

        # read in existing flux file

        obj = {}
        if os.path.isfile(path):
            obj = dvc_load(path)

        added = []
        for unk in unks:
            identifier = unk.identifier
            if identifier not in added:
                f = {'j': self.recaller.get_flux(identifier)}

                obj[identifier] = f
                added.append(identifier)

        dvc_dump(obj, path)
        self._paths.append(path)

    def _import_reduced(self, unks):
        def func(unk, prog, i, n):
            prog.change_message('Transfering {} {}/{}'.format(unk.record_id, i, n))
            ms_unk = self.recaller.find_analysis(unk.identifier, unk.aliquot, unk.step)
            keys = []
            fkeys = []
            detkeys = []
            for k, iso in unk.isotopes.items():
                miso = ms_unk.isotopes[k]
                iso.set_uvalue((miso.value, miso.error))
                det = iso.detector
                fkeys.append(det)
                fkeys.append(k)

                iso.baseline.set_uvalue((miso.baseline.value, miso.baseline.error))

                unk.set_temporary_blank(k, miso.blank.value, miso.blank.error, 'mass_spec_reduced')

                unk.set_temporary_uic_factor(det, miso.ic_factor)
                detkeys.append(det)
                keys.append(k)

            unk.dump_fits(fkeys)

            self._paths.append(unk.intercepts_path)
            self._paths.append(unk.baselines_path)

            unk.dump_blanks(keys)

            self._paths.append(unk.blanks_path)

            icfits = ['mass_spec_reduced' for _ in detkeys]
            unk.dump_icfactors(detkeys, icfits)

            self._paths.append(unk.ic_factors_path)

            meta = unk.get_meta()
            meta['comment'] = ms_unk.comment
            unk.dump_meta(meta)
            self._paths.append(unk.meta_path)

            # update the tag
            unk.set_tag({'name': ms_unk.tag, 'note': ''})
            path = self.dvc.update_tag(unk, add=False)
            self._paths.append(path)

            self.dvc.set_analysis_tag(unk, ms_unk.tag)

        progress_loader(unks, func)

    def _save(self, repo):
        dvc = self.dvc

        dvc.pull_repository(repo)
        if dvc.repository_add_paths(repo, self._paths):
            dvc.repository_commit(repo, '<{}> {}'.format(MASS_SPEC_REDUCED, self.message))
            if self.share_changes:
                dvc.push_repository(repo)

        dvc.commit()
# ============= EOF =============================================
