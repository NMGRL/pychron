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
import uuid
from itertools import groupby

from pychron.options.isochron import InverseIsochronOptions
from pychron.options.spectrum import SpectrumOptions
from pychron.pipeline.plot.editors.figure_editor import FigureEditor
from pychron.processing.analyses.analysis_group import InterpretedAgeGroup


class InterpretedAgeEditor(FigureEditor):
    def get_interpreted_ages(self):
        key = lambda x: x.group_id
        unks = sorted(self.analyses, key=key)
        # ok = 'omit_{}'.format(self.basename)

        po = self.plotter_options
        additional = {}
        if isinstance(po, SpectrumOptions):
            ek = po.plateau_age_error_kind
            pk = ''
            additional['include_j_error_in_plateau'] = po.include_j_error_in_plateau
        elif isinstance(po, InverseIsochronOptions):
            pk = 'Isochron'
            ek = po.error_calc_method
            additional['include_j_error_in_mean'] = True

        else:
            ek = po.error_calc_method
            pk = 'Weighted Mean'
            additional['include_j_error_in_individual_analyses'] = po.include_j_error
            additional['include_j_error_in_mean'] = po.include_j_error_in_mean

        def func(aa):
            return InterpretedAgeGroup(analyses=filter(lambda x: not x.is_omitted(), aa),
                                       all_analyses=aa,
                                       preferred_age_kind=pk,
                                       preferred_age_error_kind=ek,
                                       use=True,
                                       uuid=str(uuid.uuid4()),
                                       **additional)

        ias = [func(list(ans)) for gid, ans in groupby(unks, key=key)]
        return ias

# ============= EOF =============================================
