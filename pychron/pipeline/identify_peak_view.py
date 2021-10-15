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
from traits.api import HasTraits, List, Float, Any, Instance, Str, Int, Property
from traitsui.api import View, UItem, TabularEditor, InstanceEditor, HGroup, Item
from traitsui.tabular_adapter import TabularAdapter

from pychron.pychron_constants import PLUSMINUS_ONE_SIGMA, NULL_STR


class PeaksAdapter(TabularAdapter):
    columns = [("Peak Age", "peak_age"), ("Candidates", "candidates_text")]


class CandidateAdapter(TabularAdapter):
    columns = [
        ("Sample", "sample"),
        ("Material", "material"),
        ("Project", "project"),
        ("Age", "age"),
        (PLUSMINUS_ONE_SIGMA, "age_error"),
        ("Dev.", "dev"),
        ("% Dev.", "dev_percent"),
    ]

    dev_percent_text = Property

    def _get_dev_percent_text(self):
        return "{:0.2f}".format(self.item.dev_percent)


class Candidate(HasTraits):
    sample = Str
    material = Str
    project = Str
    age = Float
    age_error = Float

    def __init__(self, peak_age, arg, *args, **kw):
        super(Candidate, self).__init__(*args, **kw)

        self.id = arg[0]
        self.sample = arg[1]
        self.material = arg[2] or NULL_STR
        self.project = arg[3] or NULL_STR
        self.age = float(arg[4])
        self.age_error = float(arg[5])
        self.label = "{}({}) {}".format(self.sample, self.material, self.id)

        self.dev = peak_age - self.age
        self.dev_percent = abs(self.dev) / peak_age * 100


class Peak(HasTraits):
    peak_age = Float
    candidates = List

    def __init__(self, peak_age, candidates, *args, **kw):
        super(Peak, self).__init__(*args, **kw)

        candidates = [Candidate(peak_age, c) for c in candidates]
        self.candidates_text = ",".join([c.label for c in candidates])
        self.candidates = candidates
        self.peak_age = peak_age

    def traits_view(self):
        v = View(UItem("candidates", editor=TabularEditor(adapter=CandidateAdapter())))
        return v


class IdentifyPeakView(HasTraits):
    peaks = List
    source = None
    selected = Instance(Peak)

    threshold = Int(1, enter_set=True, auto_set=False)

    def __init__(self, peaks, *args, **kw):
        super(IdentifyPeakView, self).__init__(*args, **kw)

        self._peak_ages = peaks
        self._make_peaks(peaks)

    def _make_peaks(self, peaks=None):
        if peaks is None:
            peaks = self._peak_ages

        self.peaks = [
            Peak(p, self.source.find_candidates(p, tol=self.threshold)) for p in peaks
        ]

    def _threshold_changed(self, new):
        if new:
            self._make_peaks()

    def traits_view(self):

        v = View(
            HGroup(Item("threshold")),
            UItem(
                "peaks",
                editor=TabularEditor(adapter=PeaksAdapter(), selected="selected"),
            ),
            UItem("selected", style="custom", editor=InstanceEditor()),
            title="Candidate Associations",
            resizable=True,
            kind="livemodal",
            width=500,
            height=500,
        )
        return v


# ============= EOF =============================================
