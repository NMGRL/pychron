#===============================================================================
# Copyright 2012 Jake Ross
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
from traits.api import HasTraits, Instance, Date, Time, List, Button
from traitsui.api import View, Item, HGroup, VGroup, spring, Label
#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.database.adapters.isotope_adapter import IsotopeAdapter
from pychron.helpers.traitsui_shortcuts import listeditor


class Dosage(HasTraits):
    startdate = Date
    enddate = Date
    starttime = Time
    endtime = Time

    #     def _startdate_default(self):
    #         return datetime.now().date()
    #
    #     def _starttime_default(self):
    #         return datetime.now().time()
    #
    #     def _enddate_default(self):
    #         return datetime.now().date()
    #
    #     def _endtime_default(self):
    #         return datetime.now().time()

    def validate_dosage(self, prev_dose):
        if self.startdate is None:
            return 'Start date not set'
        if self.enddate is None:
            return 'End date not set'
        if self.starttime is None:
            return 'Start time not set'
        if self.endtime is None:
            return 'End time not set'

        if prev_dose:
            if not prev_dose.enddate <= self.startdate:
                return 'Date > Prev Date'
            if not prev_dose.endtime <= self.starttime:
                return 'Time > Prev Time'

        if not self.startdate <= self.enddate:
            return 'Start Date > End Date'

        if not self.starttime < self.endtime:
            return 'Start Time > End Time'

    def traits_view(self):
        v = View(
            HGroup(
                HGroup(
                    Item('startdate', show_label=False),
                    Item('starttime', show_label=False),
                ),
                HGroup(
                    Item('enddate', show_label=False),
                    Item('endtime', show_label=False),
                )
            )

        )

        return v


class ChronologyInput(HasTraits):
    db = Instance(IsotopeAdapter)
    dosages = List(Dosage)
    add = Button('+')
    remove = Button('-')

    def set_dosages(self, ds):
        def dose_factory(di):
            s, e = di
            return Dosage(startdate=s.date(),
                          starttime=s.time(),
                          enddate=e.date(),
                          endtime=e.time()
            )

        self.dosages = map(dose_factory, ds)

    def validate_chronology(self):
        pdi = None
        for di in self.dosages:
            err = di.validate_dosage(pdi)
            if err:
                return err
            pdi = di

    def _remove_fired(self):
        self.dosages.pop(-1)

    def _add_fired(self):
        ds = Dosage()
        pds = self.dosages[-1]
        if pds:
            ds.startdate = pds.enddate
            ds.enddate = pds.enddate

            ds.starttime = pds.endtime
            ds.endtime = pds.endtime

        self.dosages.append(ds)

    def _dosages_default(self):
        return [Dosage()]

    def traits_view(self):
        v = View(VGroup(
            HGroup(spring, Label('Start'), spring, Label('End'), spring),
            listeditor('dosages'),
            spring,
            HGroup(spring, Item('add'), Item('remove',
                                             enabled_when='len(object.dosages)>1'
            ), show_labels=False)),
                 height=350, resizable=True,
                 title='Irradiation Chronology',
                 buttons=['OK', 'Cancel']
        )
        return v

        #============= EOF =============================================
