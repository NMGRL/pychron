# ===============================================================================
# Copyright 2014 Jake Ross
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
# ===============================================================================

# ============= enthought library imports =======================
from datetime import date, time, timedelta, datetime

from traits.api import HasTraits, List, Date, Time, Float, Button
from traitsui.api import View, UItem, HGroup, VGroup, TableEditor, Item
from traitsui.table_column import ObjectColumn

from pychron.envisage.icon_button_editor import icon_button_editor


class IrradiationDosage(HasTraits):
    start_date = Date
    end_date = Date
    start_time = Time
    end_time = Time
    power = Float(1.0)

    def __init__(self, *args, **kw):
        super(IrradiationDosage, self).__init__(*args, **kw)
        # now=datetime.now().time()
        if not self.start_time:
            self.start_time = time(hour=8)
        if not self.end_time:
            self.end_time = time(hour=17)

    def _start_date_default(self):
        return date.today()

    def _end_date_default(self):
        return date.today()

    def start(self):
        return '{} {}'.format(self.start_date, self.start_time)

    def end(self):
        return '{} {}'.format(self.end_date, self.end_time)

    def make_blob(self):
        return '{}|{} {}%{} {}'.format(self.power, self.start_date, self.start_time,
                                       self.end_date, self.end_time)

    def to_tuple(self):
        print 'tooo', str(self.power), self.start(), self.end()
        return str(self.power), self.start(), self.end()

        # def validate_dosage(self, prev_dose):
        #     if self.start_date is None:
        #         return 'Start date not set'
        #     if self.end_date is None:
        #         return 'End date not set'
        #     if self.start_time is None:
        #         return 'Start time not set'
        #     if self.end_time is None:
        #         return 'End time not set'
        #
        #     if prev_dose:
        #         if not prev_dose.enddate <= self.start_date:
        #             return 'Date > Prev Date'
        #         if not prev_dose.endtime <= self.start_time:
        #             return 'Time > Prev Time'
        #
        #     if not self.start_date <= self.end_date:
        #         return 'Start Date > End Date'
        #
        #     if not self.start_time < self.end_time:
        #         return 'Start Time > End Time'


class IrradiationChronology(HasTraits):
    dosages = List(IrradiationDosage)
    add_button = Button
    remove_button = Button
    selected_dosage = IrradiationDosage
    duration = Float(8)
    apply_duration_button = Button

    def set_dosages(self, ds):
        """
        :param ds: list of 3-tuples (power, start, end)
        :return:
        """
        def dose_factory(di):
            p, s, e = di
            return IrradiationDosage(start_date=s.date(),
                                     start_time=s.time(),
                                     end_date=e.date(),
                                     end_time=e.time(), power=p)

        self.dosages = map(dose_factory, ds)

    def get_doses(self):
        """
        return a list of 3-tuples (power, start, end)
        :return:
        """
        return [ci.to_tuple() for ci in self.dosages]

    def make_blob(self):
        chronblob = '$\n'.join([ci.make_blob() for ci in self.dosages])
        return chronblob

    def _add_button_fired(self):
        dos = IrradiationDosage()
        if self.dosages:
            p = self.dosages[-1]
            dos.start_date = p.end_date
            dos.start_time = p.start_time
            dos.end_date = dos.start_date
            dos.end_time = p.end_time

        self.dosages.append(dos)

    def _remove_button_fired(self):
        if self.selected_dosage:
            if self.selected_dosage in self.dosages:
                idx = self.dosages.index(self.selected_dosage)
                self.dosages.remove(self.selected_dosage)
                if self.dosages:
                    self.selected_dosage = self.dosages[idx - 1]

    def _apply_duration_button_fired(self):
        sd = self.selected_dosage
        if sd and self.duration:
            nt = datetime.combine(sd.start_date, sd.start_time) + timedelta(hours=self.duration)
            self.selected_dosage.end_date = nt.date()
            self.selected_dosage.end_time = nt.time()

    def traits_view(self):
        tb = HGroup(icon_button_editor('add_button', 'add'),
                    icon_button_editor('remove_button', 'delete'),
                    Item('duration'),
                    icon_button_editor('apply_duration_button', 'arrow_right',
                                       tooltip='Apply "Duration" to selected row. i.e EndDateTime = StartDateTime + '
                                               'Duration'))

        cols = [ObjectColumn(name='start_date', width=100),
                ObjectColumn(name='start_time', width=100),
                ObjectColumn(name='end_date', width=100),
                ObjectColumn(name='end_time', width=100),
                ObjectColumn(name='power', width=50)]
        table = UItem('dosages', editor=TableEditor(columns=cols,
                                                    edit_on_first_click=False,
                                                    selected='selected_dosage',
                                                    sortable=False),
                      width=450)
        v = View(VGroup(tb, table))
        return v


if __name__ == '__main__':
    c = IrradiationChronology()
    c.configure_traits()
# ============= EOF =============================================

