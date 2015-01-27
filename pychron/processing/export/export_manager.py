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
from traits.api import Instance, Enum, Any, List

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.loggable import Loggable
from pychron.processing.export.export_spec import MassSpecExportSpec
from pychron.processing.export.exporter import Exporter
from pychron.processing.export.massspec_analysis_exporter import MassSpecAnalysisExporter
from pychron.processing.export.xml_analysis_exporter import XMLAnalysisExporter
from pychron.processing.export.yaml_analysis_exporter import YAMLAnalysisExporter

EX_KLASS_DICT={'MassSpec':MassSpecAnalysisExporter,
               'XML':XMLAnalysisExporter,
               'YAML':YAMLAnalysisExporter}

class ExportManager(Loggable):
    kind = Enum('XML', 'MassSpec', 'YAML')
    exporter = Instance(Exporter)
    manager=Any

    exported_analyses = List

    def export(self, ans):
        if self.exporter.start_export():
            n = len(ans)
            prog = self.manager.open_progress(n)
            for ei in ans:
                self._export_analysis(ei, prog)
                self.exported_analyses.append(ei)
            self.exporter.export()
            prog.close()
        else:
            self.warning('Export failed to start')

    # def _make_export_spec(self, ai):
        # ai = self.manager.make_analysis(ai, calculate_age=True,
        #                                 unpack=True,
        #                                 use_cache=False)

        # return self.exporter.make_spec(ai)

        # rs_name, rs_text=assemble_script_blob()
        # rs_name, rs_text = '', ''
        # rid = ai.record_id
        # exp = MassSpecExportSpec(runid=rid,
        #                  runscript_name=rs_name,
        #                  runscript_text=rs_text,
        #                  mass_spectrometer=ai.mass_spectrometer.capitalize(),
        #                  isotopes=ai.isotopes)
        #
        # exp.load_record(ai)
        # return exp

    def _exporter_default(self):
        return XMLAnalysisExporter()

    def _kind_changed(self):

        try:
            klass=EX_KLASS_DICT[self.kind]
            self.exporter=klass()
        except KeyError:
            self.warning_dialog('invalid kind {}. available={}'.format(self.kind,
                                                                       ','.join(EX_KLASS_DICT.keys())))
        # if self.kind == 'MassSpec':
        #     self.exporter = MassSpecExporter()
        # elif
        # else:
        #     self.exporter = XMLAnalysisExporter()

    def _export_analysis(self, ai, prog):
        # db=self.manager.db
        # with db.session_ctx():
        # dest=self.destination
        # espec = self._make_export_spec(ai)
        self.exporter.add(ai)
        prog.change_message('Export analysis {}'.format(ai.record_id))
# ============= EOF =============================================

