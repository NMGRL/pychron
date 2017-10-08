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
# ============= standard library imports ========================
# ============= local library imports  ==========================
from datetime import datetime

from pychron.experiment.utilities.identifier import is_special


def get_curtag():
    now = datetime.now()

    suffix = 1 if now.month > 6 else 0
    curtag = '{}{}'.format(now.strftime('%y'), suffix)
    return curtag


def populate_repository_identifiers(runs, ms, curtag, debug=None):
    if debug:
        debug('populating repository identifiers, ms={}, curtag={}'.format(ms, curtag))

    for ai in runs:
        if not ai.repository_identifier:
            repo_id = 'laboratory'
            atype = ai.analysis_type
            if atype in ('air', 'blank_air'):
                repo_id = '{}_air{}'.format(ms, curtag)
            elif atype in ('cocktail', 'blank_cocktail'):
                repo_id = '{}_cocktail{}'.format(ms, curtag)
            elif atype in ('blank_unknown', 'blank_extractionline'):
                repo_id = '{}_blank{}'.format(ms, curtag)

            if debug:
                debug('setting {} to repo={} type={}'.format(ai.runid, repo_id, atype))
            ai.repository_identifier = repo_id


def retroactive_repository_identifiers(spec, cruns, active_respository_identifier):
    if cruns is None:
        cruns = []

    if is_special(spec.identifier):
        cruns.append(spec)
        if active_respository_identifier:
            spec.repository_identifier = active_respository_identifier
    else:
        exp_id = spec.repository_identifier
        # if cruns:
        #     for c in self._cached_runs:
        #         self.datahub.maintstore.add_experiment_association(c, exp_id)
        #     self._cached_runs = []
        active_respository_identifier = exp_id

    return cruns, active_respository_identifier

# ============= EOF =============================================
