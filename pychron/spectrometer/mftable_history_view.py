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
from pychron.core.ui import set_qt

set_qt()

# ============= enthought library imports =======================
from traits.api import HasTraits, Int, Date, List, Str, Instance, Button
from traitsui.api import View, Item, TabularEditor, Controller, UItem, \
    VSplit, VGroup, spring, EnumEditor, HGroup

# ============= standard library imports ========================
# ============= local library imports  ==========================
from traitsui.tabular_adapter import TabularAdapter
from pychron.database.isotope_database_manager import IsotopeDatabaseManager


class FreeAdapter(TabularAdapter):
    columns = [('placeholder', 'placeholder')]


class FreeRow(HasTraits):
    pass


class MFTableAdapter(TabularAdapter):
    columns = [('Date', 'create_date')]


class MFTableRecord(HasTraits):
    rid = Int
    create_date = Date
    blob = Str


class MFTableHistory(HasTraits):
    items = List
    selected = Instance(MFTableRecord)
    limit = Int(10, enter_set=True, auto_set=False)
    selected_table_blob = Str
    selected_table = List
    spectrometer = Str
    spectrometers = List
    checkout_button = Button('Checkout')

    def __init__(self, connect=True, *args, **kw):
        super(MFTableHistory, self).__init__(*args, **kw)
        self.dbm = IsotopeDatabaseManager(bind=connect, connect=connect)

    def load_history(self):
        db = self.dbm.db
        self.spectrometers = [mi.name for mi in db.get_mass_spectrometers()]
        self._load_items()

    def _load_items(self):
        db = self.dbm.db
        items = db.get_mftables(self.spectrometer, limit=self.limit)

        self.items = [MFTableRecord(rid=int(i.id),
                                    create_date=i.create_date) for i in items]

    def _selected_changed(self, new):
        if new:
            if new.blob:
                blob = new.blob
            else:
                db = self.dbm.db
                item = db.get_mftable(new.rid)
                new.blob = blob = item.blob

            self._assemble_table(blob)

    def _assemble_table(self, b):
        bs = b.split('\n')
        header = bs[0].split(',')

        self.selected_adapter.columns = [(hi, hi) for hi in header]

        def make_row(li):
            r = FreeRow()
            for hi, v in zip(header, li):
                r.add_trait(hi, Str(v.strip()))
            return r

        items = [make_row(l.split(','))
                 for l in bs[1:] if l]
        self.selected_table = items

    def _spectrometer_changed(self, old, new):
        if old and new:
            self._load_items()

    def _limit_changed(self, new):
        if new:
            self._load_items()

    def _checkout_button_fired(self):
        with open(self.checkout_path, 'w') as wfile:
            hs = [hi[1] for hi in self.selected_adapter.columns]
            h = ','.join(hs)
            wfile.write('{}\n'.format(h))
            for r in self.selected_table:
                wfile.write('{}\n'.format(','.join([getattr(r, hi) for hi in hs])))


class MFTableHistoryView(Controller):
    def traits_view(self):
        self.model.selected_adapter = FreeAdapter()
        v = View(
            VGroup(HGroup(spring,
                          Item('spectrometer',
                               editor=EnumEditor(name='spectrometers')),
                          Item('limit')),
                   VSplit(UItem('items', editor=TabularEditor(adapter=MFTableAdapter(),
                                                              editable=False,
                                                              selected='selected')),
                          UItem('selected_table',
                                visible_when='selected',
                                editor=TabularEditor(adapter=self.model.selected_adapter))),
                   HGroup(spring, UItem('checkout_button', enabled_when='selected'))),
            kind='livemodal',
            buttons=['OK'],
            width=500,
            height=400,
            resizable=True)
        return v


if __name__ == '__main__':
    mfh = MFTableHistory(connect=False,
                         checkout_path='/Users/ross/Sandbox/mfcheckout.txt',
                         spectrometer='jan')
    mfh.dbm.db.trait_set(host='localhost',
                         kind='mysql',
                         username='root',
                         password='Argon',
                         name='pychrondata_dev')
    mfh.dbm.connect()
    mfh.load_history()
    #
    mv = MFTableHistoryView(model=mfh)
    mv.configure_traits()
# ============= EOF =============================================

