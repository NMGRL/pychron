#===============================================================================
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
#===============================================================================

#============= enthought library imports =======================
from traits.api import Instance, Enum, Any

#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.loggable import Loggable
from pychron.processing.export.export_spec import ExportSpec
from pychron.processing.export.exporter import MassSpecExporter, XMLExporter, Exporter


class ExportManager(Loggable):
    kind = Enum('MassSpec', 'XML')
    exporter = Instance(Exporter)
    manager=Any

    def export(self, ans):
        if self.exporter.start_export():
            n = len(ans)
            prog = self.manager.open_progress(n)
            for ei in ans:
                self._export_analysis(ei, prog)
            prog.close()

    def _make_export_spec(self, ai):
        ai = self.manager.make_analysis(ai, use_cache=False)

        # rs_name, rs_text=assemble_script_blob()
        rs_name, rs_text = '', ''
        rid = ai.record_id

        exp = ExportSpec(runid=rid,
                         runscript_name=rs_name,
                         runscript_text=rs_text,
                         mass_spectrometer=ai.mass_spectrometer.capitalize(),
                         isotopes=ai.isotopes)

        exp.load_record(ai)
        return exp

    def _exporter_default(self):
        return MassSpecExporter()

    def _kind_changed(self):
        if self.kind == 'MassSpec':
            self.exporter = MassSpecExporter()
        else:
            self.exporter = XMLExporter()

    def _export_analysis(self, ai, prog):
        # db=self.manager.db
        # with db.session_ctx():
        # dest=self.destination
        espec = self._make_export_spec(ai)
        self.exporter.add(espec)
        prog.change_message('Export analysis {}'.format(ai.record_id))
#============= EOF =============================================

