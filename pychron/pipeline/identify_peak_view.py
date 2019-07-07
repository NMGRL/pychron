# ===============================================================================
# Copyright 2019 ross
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
from traits.api import HasTraits, List, Float
from traitsui.api import View, UItem, TabularEditor
from traitsui.tabular_adapter import TabularAdapter


class PeaksAdapter(TabularAdapter):
    columns = [('Peak Age', 'peak_age'), ('Candidates', 'candidates_text')]


class Peak(HasTraits):
    peak_age = Float
    candidates = List

    def __init__(self, peak_age, candidates, *args, **kw):
        super(Peak, self).__init__(*args, **kw)
        self.candidates_text = ','.join(candidates)
        self.candidates = candidates
        self.peak_age = peak_age


class IdentifyPeakView(HasTraits):
    peaks = List

    def __init__(self, peaks, *args, **kw):
        super(IdentifyPeakView, self).__init__(*args, **kw)
        self._make_peaks(peaks)

    def _make_peaks(self, peaks):
        def find_candidates(p):
            return ['a', 'b', 'c']

        def peak_factory(p):
            candidates = find_candidates(p)
            pp = Peak(p, candidates)
            return pp

        self.peaks = [peak_factory(p) for p in peaks]

    def traits_view(self):
        v = View(UItem('peaks', editor=TabularEditor(adapter=PeaksAdapter())),
                 title='Candidate Associations',
                 resizable=True,
                 kind='livemodal',
                 width=500,
                 height=500)
        return v
# ============= EOF =============================================
