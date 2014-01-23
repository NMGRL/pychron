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
from traits.api import HasTraits, Instance, Enum, Property, \
    Str, Any, Button, List, Bool, Int
from traitsui.api import View, Item, InstanceEditor, UItem, Group, HGroup
from pyface.file_dialog import FileDialog
from pyface.constant import OK
#============= standard library imports ========================
import time
#============= local library imports  ==========================
from pychron.experiment.export.export_spec import ExportSpec
from pychron.database.isotope_database_manager import IsotopeDatabaseManager
from pychron.experiment.utilities.identifier import convert_special_name, make_runid
from pychron.experiment.automated_run.automated_run import assemble_script_blob
from pychron.processing.search.selector_manager import SelectorManager
from pychron.database.database_connection_spec import DBConnectionSpec
# from pychron.progress_dialog import myProgressDialog
import csv
from pychron.database.records.isotope_record import IsotopeRecordView
from threading import Thread
from pychron.core.ui.tabular_editor import myTabularEditor
from traitsui.tabular_adapter import TabularAdapter
from pychron.core.ui.progress_dialog import myProgressDialog

class ExportedAdapter(TabularAdapter):
    columns = [('', 'n'), ('RID', 'rid')]
#    def get_bg_color(self, *args, **kw):
#        if self.item.skipped:
#            return 'red'
#        else:
#            return 'lightgray'

class Exported(HasTraits):
    rid = Str
    n = Int
    skipped = Bool(False)

class MassSpecDestination(HasTraits):
    destination = Property
    dbconn_spec = Instance(DBConnectionSpec, ())
    def _get_destination(self):
        return self.dbconn_spec.make_connection_dict()

    def traits_view(self):
        return View(Item('dbconn_spec', show_label=False, style='custom'))

    @property
    def url(self):
        return self.dbconn_spec.make_url()

class XMLDestination(HasTraits):
    destination = Str('/Users/ross/Sandbox/exporttest2.xml')
    browse_button = Button('browse')
    def _browse_button_fired(self):
        dlg = FileDialog(action='save as')
        if dlg.open() == OK:
            self.destination = dlg.path

    def traits_view(self):
        return View(HGroup(UItem('destination', width=0.75),
                           UItem('browse_button', width=0.25)))
    @property
    def url(self):
        return self.destination


class ExportManager(IsotopeDatabaseManager):
    selector_manager = Instance(SelectorManager)
#    kind = Enum('XML', 'MassSpec')
    kind = Enum('MassSpec', 'XML')
    destination = Any

    export_button = Button('Export')
    select_data = Button('Select Data')
    data_kind = Enum('CSV', 'Database')

    records = List
    nexports = Property(Int, depends_on='records')
    exported = List
    dry_run = Bool(False)

#===============================================================================
# private
#===============================================================================
    def _export(self):
        from pychron.database.records.isotope_record import IsotopeRecord
        src = self.db

        dest = self.destination.destination

        self.info('starting {} export'.format(self.kind))
        if self.kind == 'MassSpec':
            from pychron.experiment.export.exporter import MassSpecExporter
            exp = MassSpecExporter(dest)

        else:
            from pychron.experiment.export.exporter import XMLExporter
            exp = XMLExporter(dest)

        from pyface.timer.do_later import do_later
        records = self.records
        n = len(records)
        pd = myProgressDialog(max=n + 1, size=(550, 15))
        def open_progress():
            pd.open()
            pd.center()

        do_later(open_progress)
        time.sleep(0.25)

        # make an IsotopeRecord for convenient attribute retrieval
        record = IsotopeRecord()
        st = time.time()
        for i, rec in enumerate(records):
            self.info('adding {} {} to export queue'.format(rec.record_id, rec.uuid))

#            pd.change_message('Adding {}/{} {}    {}'.format(i + 1, n, rec.record_id, rec.uuid))
            do_later(pd.change_message, 'Adding {}/{} {}    {}'.format(i + 1, n, rec.record_id, rec.uuid))

            # reusing the record object is 45% faster than making a new one each iteration
            # get a dbrecord for this analysis
            record._dbrecord = src.get_analysis(rec.uuid, key='uuid')
            e = Exported(rid=rec.record_id, n=i + 1)
            if record.load_isotopes():
                spec = self._make_spec(record)
                if spec:
                    if not exp.add(spec):
                        e.skipped = True
            else:
                e.skipped = True
                self.info('skipping {} {}'.format(rec.record_id, rec.uuid))

            self.exported.append(e)
            do_later(pd.increment)


        do_later(pd.change_message, 'Exporting...')
#        pd.change_message('Exporting...')
        self.info('exporting to {}'.format(self.destination.url))
        if self.dry_run:
            # database rollback doesnt work. Mass Spec requirements break true transaction paradigm
            # and numerous flushes are required for each analysis added
            self.info('dry run... export would happen here')
            exp.rollback()
        else:
            exp.export()

        do_later(pd.close)
#        pd.increment()
#
        t = time.time() - st
        self.info('export complete. exported {} analyses in {:0.2f}s'.format(n, t))

    def _make_spec(self, rec):
        # make script text
        scripts = []
        kinds = []
        ext = rec.extraction
        if ext and ext.script:
            scripts.append((ext.script.name, ext.script.blob))
            kinds.append('extraction')
        meas = rec.measurement
        if meas and meas.script:
            scripts.append((meas.script.name, meas.script.blob))
            kinds.append('measurement')

        scriptname, scripttxt = assemble_script_blob(scripts, kinds)

        # make a new ExportSpec

        if rec.mass_spectrometer:
            spectrometer = 'Pychron {}'.format(rec.mass_spectrometer.capitalize())
        else:
            r = make_runid(rec.labnumber, rec.aliquot, rec.step)
            self.info('no mass spectrometer specified. Cannot import {}'.format(r))
            return

        es = ExportSpec(runid=convert_special_name(rec.labnumber),
                        mass_spectrometer=spectrometer,
                        runscript_name=scriptname,
                        runscript_text=scripttxt
                        )

        # load spec with values from rec
        es.load_record(rec)

        # load spec with other values from rec
        for k in rec.isotope_keys:
            iso = rec.isotopes[k]
            xs, ys = iso.xs, iso.ys
            sig = zip(xs, ys)

            bxs, bys = iso.baseline.xs, iso.baseline.ys
            base = zip(bxs, bys)
            es.signals.append(sig)
            es.baselines.append(base)
            es.detectors.append((iso.detector, iso.name))
            es.signal_intercepts.append(iso.uvalue)
            es.baseline_intercepts.append(iso.baseline.uvalue)
            es.signal_fits.append(iso.fit)
            es.baseline_fits.append('Average Y')

            es.blanks.append(iso.blank.uvalue)

        return es
#===============================================================================
# handlers
#===============================================================================
    def _kind_changed(self):
        if self.kind == 'MassSpec':
            klass = MassSpecDestination
        else:
            klass = XMLDestination
        self.destination = klass()

    def _select_data_fired(self):
        if self.data_kind == 'Database':
            d = self.selector_manager
            if self.db.connect():
                info = d.edit_traits(kind='livemodal')
                if info.result:
                    self.records = d.selected_records
#                    d.selected_records = []
        else:
            p = '/Users/ross/Sandbox/exportruns.csv'
            with open(p, 'r') as fp:
                reader = csv.reader(fp, delimiter=',')
                header = reader.next()

                uuid_idx = header.index('uuid')
                record_id_idx = header.index('RID')
#                for row in reader:
                self.records = [IsotopeRecordView(uuid=row[uuid_idx],
                                                  record_id=row[record_id_idx],
                                                  ) for row in reader]  # [778:779]

    def _export_button_fired(self):
        if self.records:
            t = Thread(target=self._export)
            t.start()
#            self._export(self.records)
        else:
            self.warning_dialog('Not connected to a source database')

    def _test_fired(self):
        self._export('220bffbe-c37d-4ff1-8128-3f329233fa2e')

#===============================================================================
# views
#===============================================================================
    def traits_view(self):
        v = View(UItem('kind'),
                 UItem('destination',
                      editor=InstanceEditor(),
                      style='custom',),
                 HGroup(UItem('select_data'), UItem('data_kind')),
                 Item('nexports', format_str='%05i', style='readonly', label='Num. Analyses to Export'),
                 Group(
                       UItem('exported',
                             editor=myTabularEditor(adapter=ExportedAdapter(),
                                                    editable=False, operations=[])
#                             editor=ListStrEditor(editable=False,
#                                                  drag_move=True,
#                                                  operations=[],
#                                                  horizontal_lines=True),
                             ),
                       show_border=True,
                       label='Exported'
                       ),
                 Group(
                       Item('dry_run'),
                       show_border=True,
                       label='Options'),
                 UItem('export_button'),
                 height=500,
                 width=400,
                 title='Exporter',
                 resizable=True
                 )
        return v
#===============================================================================
# property get/set
#===============================================================================
    def _get_nexports(self):
        return len(self.records)

#===============================================================================
# defaults
#===============================================================================
    def _selector_manager_default(self):
        db = self.db
        d = SelectorManager(db=db)
        return d

    def _destination_default(self):
        if self.kind == 'MassSpec':
            klass = MassSpecDestination
        else:
            klass = XMLDestination
        return klass()

if __name__ == '__main__':
    from pychron.core.helpers.logger_setup import logging_setup
    logging_setup('em')

    em = ExportManager()
    em.kind = 'MassSpec'
#    em.dry_run = True

    em.db.kind = 'mysql'
    em.db.name = 'pychrondata'
    em.db.host = 'localhost'
    em.db.username = 'root'
    em.db.password = 'Argon'
    em.db.connect()


    em.destination.dbconn_spec.host = '129.138.12.160'
    em.destination.dbconn_spec.database = 'massspecdata'
    em.destination.dbconn_spec.username = 'root'
    em.destination.dbconn_spec.password = 'DBArgon'
    em.configure_traits()
#============= EOF =============================================
