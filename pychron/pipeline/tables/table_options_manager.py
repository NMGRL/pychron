# ===============================================================================
# Copyright 2020 ross
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
import os

from traits.api import Instance

from pychron.globals import globalv
from pychron.options.options_manager import BaseOptionsManager, OptionsManager
from pychron.paths import paths
from pychron.pipeline.tables.xlsx_table_options import XLSXAnalysisTableWriterOptions


class TableOptionsManager(OptionsManager):
    selected_options = Instance(XLSXAnalysisTableWriterOptions)
    options_klass = XLSXAnalysisTableWriterOptions

    # def _save(self, name, obj):
    #     obj.set_persistence_path(self._pname(name, '.json'))
    #     obj.dump()

    # def _selected_changed(self, new):
    #     if new:
    #         obj = self.options_klass(self._pname(new, '.json'))
    #         self.selected_options = obj

    @property
    def persistence_root(self):
        return os.path.join(paths.table_options_dir, globalv.username)


# ============= EOF =============================================
