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
from operator import attrgetter

from traits.api import Instance

from pychron.core.helpers.iterfuncs import groupby_repo, groupby_key
from pychron.dvc.dvc import DVC
from pychron.mass_spec.mass_spec_recaller import MassSpecRecaller
from pychron.pipeline.nodes.base import BaseNode


class MassSpecReduced(BaseNode):
    recaller = Instance(MassSpecRecaller)
    dvc = Instance(DVC)

    def run(self, state):
        key = attrgetter('repository_identifier')
        for repo, unks in groupby_repo(state.unknowns):
            # freeze flux
            self._freeze_flux(repo, unks)
            self._import_reduced(repo, unks)

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
            pass

    def _import_reduced(self, repo, unks):
        for unk in unks:
            ms_unk = self.recaller.find_analysis(unk.identifier, unk.aliquot, unk.step)
            self._import_intercepts(unk, ms_unk)

            # self._import_baselines()
            # self._import_blanks()
            # self._import_icfactors()

    def _import_intercepts(self, unk, ms_unk):
        for k, iso in unk.isotopes.items():
            miso = ms_unk.isotopes[k]
            iso.set_uvalue(miso.value, miso.error)
            iso.baseline.set_uvalue(miso.value, miso.error)
            iso.blank.set_uvalue(miso.value, miso.error)

    def save(self, repo, unks):
        pass

# ============= EOF =============================================
