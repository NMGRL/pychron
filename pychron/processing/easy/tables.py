# ===============================================================================
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
# ===============================================================================

# ============= enthought library imports =======================

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.experiment.easy_parser import EasyParser
from pychron.core.helpers.filetools import unique_path
from pychron.processing.easy.base_easy import BaseEasy
from pychron.processing.tasks.tables.editors.fusion.fusion_table_editor import FusionTableEditor
from pychron.processing.tasks.tables.editors.step_heat.step_heat_table_editor import StepHeatTableEditor


class EasyTables(BaseEasy):
    def _save_fusion(self, editor, root, ident):
        self._save_table(editor, root, ident, 'fusion')

    def _save_step_heat(self, editor, root, ident):
        self._save_table(editor, root, ident, 'stepheat')

    def _save_table(self, editor, root, ident, tag):
        ft = ('pdf', 'xls', 'csv')
        sft = ', '.join(ft[:-1])
        sft = '{} or {}'.format(sft, ft[-1])
        for ext in self._file_types:

            if ext not in ft:
                self.warning('Invalid file type "{}". Use "{}"'.format(ext, sft))
            p, _ = unique_path(root, '{}_{}_table'.format(tag, ident), extension='.{}'.format(ext))
            editor.save_file(p, title='Ar/Ar Step heat data')

    def make_tables(self):
        ep = EasyParser()
        doc = ep.doc('tables')
        projects = doc['projects']
        self._file_types = doc['file_types']

        ieditor = FusionTableEditor(processor=self)
        seditor = StepHeatTableEditor(processor=self)
        root = self._make_root(ep)
        self._make(projects, root, ieditor, seditor, 'Table')


# ============= EOF =============================================
