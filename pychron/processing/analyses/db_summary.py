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
from traits.api import HasTraits, Event, Property, List
from traitsui.api import View, Item, UItem, VSplit, HSplit, VGroup
from pychron.processing.analyses.summary import AnalysisSummary
from pychron.ui.qt.text_table_editor import TextTableEditor
from pychron.processing.analyses.adapter import AnalysisSummaryAdapter, RawAdapter, \
    AgeAdapter, SignalAdapter
from pychron.experiment.display_signal import DisplaySignal, DisplayEntry
#============= standard library imports ========================
#============= local library imports  ==========================

class DBAnalysisSummary(AnalysisSummary):
    update_needed = Event
    signals = Property(List, depends_on='model, update_needed')
    raw_signals = Property(List, depends_on='model, update_needed')
    def _get_raw_signals(self):
        return self._get_signal_values()

    def _get_signals(self):
        record = self.model
        ec = record.get_error_component('j')
        return self._get_signal_values() + [DisplayEntry(isotope='J',
                                                 error_component=ec
                                                 )]

    def _get_signal_values(self):
        model = self.model
        def factory(k):
            iso = model.isotopes[k]
            name = iso.name
            det = iso.detector
            fit = iso.fit

            icv, ice = model.get_ic_factor(det)

            rv, re = iso.value, iso.error
            bv, be = iso.baseline.value, iso.baseline.error
            blv, ble = iso.blank.value, iso.blank.error
            s = iso.get_corrected_value()
            if fit:
                fit = fit[0].upper()

            return DisplaySignal(isotope=name,
                                   detector=det,
                                   raw_value=rv,
                                   raw_error=re,
                                   fit=fit,
                                   baseline_value=bv,
                                   baseline_error=be,
                                   blank_value=blv,
                                   blank_error=ble,
                                   signal_value=s.nominal_value,
                                   signal_error=s.std_dev,
                                   error_component=model.get_error_component(k),
                                   ic_factor_value=icv,
                                   ic_factor_error=ice
                                   )

        keys = model.isotope_keys
#         isotopes = []
#         return isotopes
        return [factory(k) for k in keys]
    def traits_view(self):
        ODD_COLOR = '#CCFFFF'
        BG_COLOR = 'light yellow'
        HEADER_COLOR = 'lightgray'
        summary = UItem('model',
                              editor=TextTableEditor(adapter=AnalysisSummaryAdapter(),
                                                     bg_color=BG_COLOR
                                                     ),
                              height=0.3
                              )

        raw = UItem('raw_signals',
                           editor=TextTableEditor(adapter=RawAdapter(),
                                                 bg_color=BG_COLOR,
                                                 odd_color=ODD_COLOR,
                                                 header_color=HEADER_COLOR,
                                                 ),
                          height=0.3
                          )
        signal = UItem('signals', editor=TextTableEditor(adapter=SignalAdapter(),
                                                               bg_color=BG_COLOR,
                                                               odd_color=ODD_COLOR,
                                                               header_color=HEADER_COLOR
                                                ),
                          height=0.3,
                          width=0.75
                      )

        '''
            changes to the intensities will not trigger this editor to update
            use "refresh" extended trait name to force editor to redraw.  
        '''
        age = UItem('model',
                     editor=TextTableEditor(adapter=AgeAdapter(),
                                               bg_color=BG_COLOR,
                                               refresh='update_needed'
                                               ),
                        width=0.25
                        )

        v = View(
                 VSplit(
                        summary,
                        VGroup(raw,
                               HSplit(
                                      signal,
                                      age
                                      )
                               )
                        )
                 )
        return v
#============= EOF =============================================
