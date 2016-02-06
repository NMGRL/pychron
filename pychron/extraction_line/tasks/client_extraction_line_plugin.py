# ===============================================================================
# Copyright 2015 Jake Ross
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
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.envisage.initialization.initialization_parser import InitializationParser
from pychron.extraction_line.client_extraction_line_manager import ClientExtractionLineManager
from pychron.extraction_line.pyscript_runner import RemotePyScriptRunner
from pychron.extraction_line.tasks.client_extraction_line_preferences import ClientExtractionLinePreferencesPane
from pychron.extraction_line.tasks.extraction_line_plugin import ExtractionLinePlugin
from pychron.extraction_line.tasks.extraction_line_preferences import ConsolePreferencesPane


class ClientExtractionLinePlugin(ExtractionLinePlugin):
    id = 'pychron.client_extraction_line'
    name = 'ClientExtractionLine'
    extraction_line_manager_klass = ClientExtractionLineManager

    def _runner_factory(self):

        ip = InitializationParser()
        elm = ip.get_plugin('ClientExtractionLine', category='hardware')
        runner = elm.find('runner')
        if runner is None:
            self.warning_dialog('Script Runner is not configured in the Initialization file. See documentation')
            return

        host, port, kind, frame = None, None, None, None

        if runner is not None:
            comms = runner.find('communications')
            host = comms.find('host')
            port = comms.find('port')
            kind = comms.find('kind')
            frame = comms.find('message_frame')

        if host is not None:
            host = host.text  # if host else 'localhost'
        if port is not None:
            port = int(port.text)  # if port else 1061
        if kind is not None:
            kind = kind.text  # if kind else 'udp'
        if frame is not None:
            frame = frame.text

        runner = RemotePyScriptRunner(host, port, kind, frame)
        return runner

    def _preferences_panes_default(self):
        return [ClientExtractionLinePreferencesPane, ConsolePreferencesPane]

# ============= EOF =============================================



