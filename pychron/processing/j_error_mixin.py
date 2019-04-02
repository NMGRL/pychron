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
from traits.api import HasTraits, Bool
from traitsui.api import HGroup, Item

from pychron.persistence_loggable import dumpable

J_ERROR_GROUP = HGroup(Item('include_j_position_error', label='Include Position Error',
                            tooltip='Include J position error in the analytical error for each individual analysis.'),
                       Item('include_j_error_in_mean', label='Include in Mean',
                            tooltip='Include J error in the mean age error'),
                       show_border=True,
                       label='J Uncertainty')


class JErrorMixin(HasTraits):
    include_j_position_error = dumpable(Bool(False))
    include_j_error_in_mean = dumpable(Bool(True))
    # _suppress = False
    #
    # def _include_j_position_error_analyses_changed(self, new):
    #     if self._suppress:
    #         return
    #
    #     if new:
    #         self._suppress = True
    #         self.include_j_error_in_mean = False
    #         self._suppress = False
    #
    # def _include_j_error_in_mean_changed(self, new):
    #     if self._suppress:
    #         return
    #
    #     if new:
    #         self._suppress = True
    #         self.include_j_error_in_individual_analyses = False
    #         self._suppress = False

# ============= EOF =============================================
