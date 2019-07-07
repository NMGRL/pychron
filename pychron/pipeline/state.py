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
from __future__ import absolute_import

from traits.api import HasTraits, List, Bool, Any, Set, Str, Dict


def get_detector_set(ans):
    return {iso.detector for ai in ans for iso in ai.itervalues()}


def get_isotope_set(ans):
    return {k for ai in ans for k in ai.isotope_keys}


class EngineState(HasTraits):
    unknowns = List
    references = List

    unknown_positions = List
    monitor_positions = List

    decay_constants = Dict

    tables = List
    editors = List

    saveable_keys = List
    saveable_fits = List
    saveable_irradiation_positions = List
    delete_existing_icfactors = Bool

    veto = Any
    canceled = Bool
    run_groups = Dict

    iso_evo_results = List

    modified_projects = Set
    modified = False
    dbmodified = False

    geometry = List
    level = Str
    irradiation = Str

    report_path = None

    mdd_workspace = None


# ============= EOF =============================================
