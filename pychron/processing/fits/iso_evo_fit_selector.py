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

#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.processing.fits.filter_fit_selector import FilterFitSelector


class IsoEvoFitSelector(FilterFitSelector):
    default_error_type = 'SEM'
    def load_fits(self, keys, fits):
        bs = ['{}bs'.format(ki) for ki in keys]
        bfs = ['average' for fi in fits]

        super(IsoEvoFitSelector, self).load_fits(keys + bs, fits + bfs)

    # def traits_view(self):
    #     v = View(
    #         self
    #         self._get_fit_group())
    #     return v

        #============= EOF =============================================
