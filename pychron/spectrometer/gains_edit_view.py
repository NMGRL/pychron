# ===============================================================================
# Copyright 2014 Jake Ross
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
from traits.api import HasTraits, Button, Str, Int, Bool, Float, List, Any, Date
from traitsui.api import View, Item, UItem, HGroup, VGroup, HSplit, InstanceEditor, \
    TabularEditor
from pyface.message_dialog import information
from traitsui.editors import ListEditor
from traitsui.item import Readonly, UReadonly
from traitsui.tabular_adapter import TabularAdapter
from traitsui.handler import Controller
# ============= standard library imports ========================
from datetime import datetime
# ============= local library imports  ==========================
from pychron.core.helpers.formatting import floatfmt
from pychron.envisage.icon_button_editor import icon_button_editor


class Gain(HasTraits):
    detector = Str
    gain = Float
    strvalue = Str


class GainsModel(HasTraits):
    histories = List
    selected = Any
    db = Any
    apply_history_button = Button
    apply_button = Button
    spectrometer = Any

    def _apply_button_fired(self):
        gains = self.spectrometer.set_gains()
        if gains:
            db = self.db
            with db.session_ctx():
                hashkey = db.make_gains_hash(gains)
                hist=db.get_gain_history(hashkey)
                if not hist:
                    hist = db.add_gain_history(hashkey)
                    for d, v in gains:
                        db.add_gain(d, v, hist)

                hist.applied_date=datetime.now()

            gainstr = '\n'.join(['{} {}'.format(*g) for g in gains])
            information(None, 'Gains set\n\n{}'.format(gainstr))

    def _apply_history_button_fired(self):
        if self.spectrometer:
            self.spectrometer.set_gains(gains=self.selected.gains,
                                        history=self.selected)
        db = self.db
        with db.session_ctx():
            hist = db.get_gain_history(self.selected.hashkey)
            hist.applied_date = datetime.now()

        information(None, 'Gains update to {}'.format(self.selected.create_date))

    def _selected_changed(self, new):
        if not new.gains:
            db = self.db
            with db.session_ctx():
                hist = db.get_gain_history(new.hashkey)
                self.selected.gains = [Gain(detector=gi.detector.name,
                                            strvalue=floatfmt(gi.value),
                                            gain=gi.value)
                                       for gi in hist.gains]

    def load_histories(self):
        db = self.db
        with db.session_ctx():
            hists = db.get_gain_histories()
            self.histories = [GainHistory(create_date=hi.create_date,
                                          applied_date=hi.applied_date,
                                          hashkey=hi.hash,
                                          username=hi.user.name) for hi in hists]


class GainHistoryAdapter(TabularAdapter):
    columns = [('Date', 'create_date'), ('User', 'username')]
    create_date_width = Int(200)


class GainAdapter(TabularAdapter):
    columns = [('Name', 'detector'), ('Gain', 'strvalue')]


class GainHistory(HasTraits):
    create_date = Date
    applied_date = Date
    username = Str

    hashkey = Str
    gains = List


class GainsEditView(Controller):
    def traits_view(self):
        a = UItem('histories', editor=TabularEditor(adapter=GainHistoryAdapter(),
                                                    editable=False,
                                                    selected='selected'))
        b = UItem('selected',
                  style='custom',
                  editor=InstanceEditor(view=View(UItem('gains',
                                                        editor=TabularEditor(editable=False,
                                                                             adapter=GainAdapter())))))

        dview = View(HGroup(UReadonly('name'), 'gain'))
        egrp = VGroup(
            HGroup(icon_button_editor('apply_button', 'apply')),
            UItem('object.spectrometer.detectors',
                  editor=ListEditor(mutable=False,
                                    style='custom',
                                    editor=InstanceEditor(view=dview))),
            show_border=True,
            label='Edit Detector Gains')

        v = View(VGroup(HGroup(icon_button_editor('apply_history_button', 'apply',
                                                  tooltip='Set gains to values stored with the selected history',
                                                  enabled_when='selected')),
                        HSplit(a, b),
                        egrp),
                 width=650,
                 title='View Detector Gain Histories',
                 resizable=True)
        return v


if __name__ == '__main__':
    class Detector(HasTraits):
        name = Str
        gain = Float


    class Spectrometer(HasTraits):
        detectors = List

    spec = Spectrometer()
    spec.detectors = [Detector(name='H1'), Detector(name='AX')]

    from pychron.database.adapters.isotope_adapter import IsotopeAdapter

    db = IsotopeAdapter(name='pychrondata_dev',
                        kind='mysql',
                        host='localhost',
                        username='root',
                        password='Argon')
    db.connect()
    # hist = [GainHistory(create_date=datetime.fromtimestamp(i),) for i in range(10)]
    gv = GainsModel(db=db, spectrometer=spec)
    gv.load_histories()
    gev = GainsEditView(model=gv)
    gev.configure_traits()
# ============= EOF =============================================



