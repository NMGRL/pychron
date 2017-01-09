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
from traits.api import HasTraits, Str, Float, Property, List, Instance, Dict
from traitsui.api import View, UItem, Item, HGroup, VGroup, EnumEditor, TabularEditor
from traitsui.tabular_adapter import TabularAdapter

from pychron.envisage.tasks.base_editor import BaseTraitsEditor
from pychron.experiment.utilities.detector_ic import make_items, get_columns
from pychron.processing.analyses.view.detector_ic_view import DetectorICTabularAdapter
from pychron.pychron_constants import DETECTOR_ORDER, DETECTOR_IC


class ResultsAdapter(TabularAdapter):
    columns = [('Detector', 'detector'), ('Current Gain', 'current_gain'),
               ('Adj.', 'gfactor'), ('New Gain', 'new_gain')]


class GainCalibrationResult(HasTraits):
    detector = Str
    current_gain = Float
    gfactor = Float
    new_gain = Property

    def _get_new_gain(self):
        return self.current_gain * self.gfactor


class GainCalibrationEditor(BaseTraitsEditor):
    dvc = Instance('pychron.dvc.dvc.DVC')

    lhs_ms = Str
    lhs_available_ms = List
    lhs_runid = Str
    lhs_runids = List

    rhs_ms = Str
    rhs_available_ms = List
    rhs_runid = Str
    rhs_runids = List

    all_ms = List
    results = List

    lhs_items = List
    rhs_items = List
    _isotope_key = 'Ar40'
    tabular_adapter = Instance(DetectorICTabularAdapter, ())
    gains_dict = Dict

    def initialize(self):
        ms = self.dvc.get_mass_spectrometer_names()
        self.all_ms = ms
        self.lhs_available_ms = ms
        self.rhs_available_ms = ms

    # private
    def _get_analysis(self, rid):

        args = rid.split('-')
        ln = '-'.join(args[:-1])
        a = args[-1]
        try:
            int(a[-1])
            s = None
        except ValueError:
            s = a[-1]
        an = self.dvc.get_analysis_runid(ln, a, s)
        dan = self.dvc.make_analyses((an,))[0]
        return dan

    def _calculate(self):
        if not self.lhs_runid:
            return

        db = self.dvc.db
        if self.rhs_runid:
            rhs_an = self._get_analysis(self.rhs_runid)
            self.rhs_items = make_items(rhs_an.isotopes)

        lhs_an = self._get_analysis(self.lhs_runid)
        self.lhs_items = make_items(lhs_an.isotopes)

        isotopes = [lhs_an.isotopes[k] for k in lhs_an.isotope_keys if k.startswith(self._isotope_key)]

        detcols = get_columns(isotopes)

        self.tabular_adapter.columns = [('', 'name'), ('Intensity', 'intensity')] + detcols
        self._make_results()

    def _get_current_gains(self, ms):
        # print gains_dict
        # self.current_gains = [gains_dict[k] for k in DETECTOR_ORDER]
        self.gains_dict = self.dvc.meta_repo.get_gains(ms)

    def _make_results(self):
        refdet = 'H1'
        results = [GainCalibrationResult(current_gain=self.gains_dict.get(k, 1), detector=k) for k in DETECTOR_ORDER]

        """
            lv_i = (AX/H1)o
            rv_i = (AX/H1)j

        """
        for i, r in enumerate(results):
            li = self.lhs_items[i]
            ri = self.rhs_items[i]
            lv = getattr(li, refdet)
            rv = getattr(ri, refdet)

            r.gfactor = rv / lv

        self.results = results

    # handlers
    def _lhs_ms_changed(self, new):
        if new:
            self.rhs_available_ms = [m for m in self.all_ms if m != new]
            if not self.rhs_ms and self.rhs_available_ms:
                self.rhs_ms = self.rhs_available_ms[0]

            self.lhs_runids = self._get_runids(new)
            if not self.lhs_runid and self.lhs_runids:
                self.lhs_runid = self.lhs_runids[0]

    def _rhs_ms_changed(self, new):
        if new:
            self._get_current_gains(new)

            self.lhs_available_ms = [m for m in self.all_ms if m != new]
            if not self.lhs_ms and self.lhs_available_ms:
                self.lhs_ms = self.lhs_available_ms[0]

            self.rhs_runids = self._get_runids(new)
            if not self.rhs_runid and self.rhs_runids:
                self.rhs_runid = self.rhs_runids[0]

    def _lhs_runid_changed(self, new):
        self._calculate()

    def _rhs_runid_changed(self, new):
        self._calculate()

    def _get_runids(self, ms):
        db = self.dvc.db
        ans = db.get_analyses(analysis_type=DETECTOR_IC,
                              mass_spectrometer=ms,
                              reverse_order=True
                              )
        return [ai.record_id for ai in ans]

    def traits_view(self):
        editor = TabularEditor(adapter=self.tabular_adapter,
                               editable=False,
                               stretch_last_section=False)

        l_grp = VGroup(VGroup(Item('lhs_ms', width=200, editor=EnumEditor(name='lhs_available_ms')),
                              Item('lhs_runid', width=200, editor=EnumEditor(name='lhs_runids'))),
                       UItem('lhs_items', editor=editor))

        r_grp = VGroup(VGroup(Item('rhs_ms', width=200, editor=EnumEditor(name='rhs_available_ms')),
                              Item('rhs_runid', width=200, editor=EnumEditor(name='rhs_runids'))),
                       UItem('rhs_items', editor=editor))

        results_grp = VGroup(UItem('results', editor=TabularEditor(adapter=ResultsAdapter(),
                                                                   editable=False)))

        v = View(VGroup(HGroup(l_grp, r_grp), results_grp),
                 title='Configure Gain Calibration',
                 buttons=['OK', 'Cancel'])
        return v

# ============= EOF =============================================
