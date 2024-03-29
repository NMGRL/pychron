# ===============================================================================
# Copyright 2018 ross
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
from pychron.pipeline.editors.audit_editor import AuditEditor
from pychron.pipeline.nodes.base import BaseNode


class AuditNode(BaseNode):
    auto_configure = False
    name = "Audit"
    configurable = False

    def run(self, state):
        editor = AuditEditor()
        editor.set_unks_refs(state.unknowns, state.references)

        state.editors.append(editor)


# ============= EOF =============================================
