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
from traits.api import HasTraits, List, Bool, Any, Property, cached_property, Set
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.core.helpers.isotope_utils import sort_isotopes


def get_detector_set(ans):
    return {iso.detector for ai in ans for iso in ai.isotopes.itervalues()}


class EngineState(HasTraits):
    unknowns = List
    references = List
    flux_monitors = List

    editors = List
    has_references = Bool
    has_flux_monitors = Bool
    saveable_keys = List
    saveable_fits = List
    # user_review = Bool
    veto = Any
    udetectors = Property(depends_on='unknowns[]')
    rdetectors = Property(depends_on='references[]')
    union_detectors = Property(depends_on='udetectors, rdetectors')
    iso_evo_results = List

    modified_projects = Set
    modified = False
    dbmodified = False

    @cached_property
    def _get_udetectors(self):
        return get_detector_set(self.unknowns)

    @cached_property
    def _get_rdetectors(self):
        return get_detector_set(self.references)

    @cached_property
    def _get_union_detectors(self):
        x = set(self.udetectors).union(self.rdetectors)
        return sort_isotopes(x)

# ============= EOF =============================================
