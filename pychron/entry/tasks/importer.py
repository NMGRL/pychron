# ===============================================================================
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
# ===============================================================================

# ============= enthought library imports =======================
from traits.api import Enum, Instance, Str, Button, List, Any, Bool, Property, Event, cached_property, Int
# ============= standard library imports ========================
from collections import namedtuple
import time

# ============= local library imports  ==========================
from pychron.core.progress import open_progress
from pychron.entry.loaders.extractor import Extractor
from pychron.entry.loaders.mass_spec_extractor import MassSpecExtractor
from pychron.loggable import Loggable
from pychron.pychron_constants import NULL_STR
from pychron.core.ui.qt.thread import Thread
from pychron.core.ui.gui import invoke_in_main_thread

records = namedtuple('Record', 'name')


class ImporterModel(Loggable):
    dest = Any

    data_source = Enum('MassSpec', 'File')
    extractor = Instance(Extractor)
    import_kind = Enum('---', 'irradiation', 'rid_list')

    import_button = Button('Import')
    open_button = Button('Open')
    names = List
    readable_names = Property(depends_on='names, names[]')
    selected = Any
    text_selected = Str
    scroll_to_row = Int
    imported_names = List
    custom_label1 = Str('Imported')
    filter_str = Str(enter_set=True, auto_set=False)
    progress = Int

    include_analyses = Bool(False)
    include_blanks = Bool(False)
    include_airs = Bool(False)
    include_cocktails = Bool(False)

    #    include_analyses = Bool(True)
    #    include_blanks = Bool(True)
    #    include_airs = Bool(True)
    #    include_cocktails = Bool(True)
    include_list = List
    update_irradiations_needed = Event
    dry_run = Bool(False)

    def _progress_message(self, pd, m):
        invoke_in_main_thread(pd.change_message, m)

    def _do_import(self, selected, pd):
        # func = getattr(self.extractor, 'import_{}'.format(self.import_kind))

        st = time.time()
        dest = self.dest
        with dest.session_ctx(commit=not self.dry_run):
            for irrad, levels in selected:
                # pd.max = len(levels) + 2
                self._progress_message(pd, 'Importing {} {}'.format(irrad, levels))
                r = self.extractor.import_irradiation(dest,
                                                      irrad,
                                                      pd,
                                                      include_analyses=self.include_analyses,
                                                      include_blanks=self.include_blanks,
                                                      include_airs=self.include_airs,
                                                      include_cocktails=self.include_cocktails,
                                                      dry_run=self.dry_run,
                                                      include_list=levels)

                if r:
                    self.imported_names.append(r)
                    self._progress_message(pd,
                                           'Imported {} {} successfully'.format(irrad, levels))
                else:
                    self._progress_message(pd,
                                           'Import {} {} failed'.format(irrad, levels))

        self.info('====== Import Finished elapsed_time= {}s======'.format(int(time.time() - st)))
        return True
        # if self.imported_names:
        #    self.update_irradiations_needed = True

    @cached_property
    def _get_readable_names(self):
        return [ni.name for ni in self.names]

    def _text_selected_changed(self):
        txt = self.text_selected
        if ',' in txt:
            txt = txt.split(',')
        elif ':' in txt:

            start, end = txt.split(':')
            shead, scnt = start.split('-')
            ntxt = []
            if not end:
                return

            for i in range(int(end) - int(scnt) + 1):
                ntxt.append('{}-{}'.format(shead, int(scnt) + i))

            txt = ntxt
        else:
            txt = [txt]

        def get_name(name):
            return next((ni for ni in self.names if ni.name == name), None)

        sel = []
        for ti in txt:
            name = get_name(ti)
            if name is not None:
                sel.append(name)
        if sel:
            self.selected = sel
            self.scroll_to_row = self.names.index(sel[0])

    def _filter_str_changed(self):
        func = getattr(self.extractor, 'get_{}s'.format(self.import_kind))
        self.names = func(filter_str=self.filter_str)

    def _open_button_fired(self):
        p = self.open_file_dialog()
        if p:
            with open(p, 'r') as rfile:
                rids = [records(ri.strip()) for ri in rfile.read().split('\n')]
                self.names = rids

    _import_thread = None

    def _import_button_fired(self):
        self.do_import()

    def do_import(self, new_thread=True):
        if self.import_kind != NULL_STR:
            selected = self.selected
            #             if selected:
            if selected:
                if not isinstance(selected[0], tuple):
                    selected = [(si.name, tuple()) for si in selected]
                    #                if self._import_thread and self._import_thread.isRunning():
                #                    return

                if self.dest.connect():
                    # clear imported
                    self.imported_names = []
                    #                    self.db.reset()

                    # self.db.save_username = 'jake({})'.format(self.db.username)
                    self.info('====== Import Started  ======')
                    self.info('user name= {}'.format(self.dest.save_username))
                    # get import func from extractor

                    n = len(selected) * 2
                    pd = open_progress(n=n)

                    if new_thread:
                        t = Thread(target=self._do_import, args=(selected, pd))
                        t.start()
                        self._import_thread = t
                        return t
                    else:
                        self._do_import(selected, pd)
                        return True

    def _data_source_changed(self):
        if self.data_source == 'MassSpec':
            self.extractor = MassSpecExtractor()
        else:
            self.extractor = None

    def _import_kind_changed(self):
        try:
            func = getattr(self.extractor, 'get_{}s'.format(self.import_kind))
            self.names = func()
        except AttributeError:
            pass

    def _extractor_default(self):
        return MassSpecExtractor()

    def _data_source_default(self):
        return 'MassSpec'


if __name__ == '__main__':
    im = ImporterModel()
    im.configure_traits()
# ============= EOF =============================================
