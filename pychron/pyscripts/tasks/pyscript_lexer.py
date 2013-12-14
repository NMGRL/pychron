#===============================================================================
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
#===============================================================================

#============= enthought library imports =======================
from pygments.lexers.agile import PythonLexer
from pygments.token import Name

#============= standard library imports ========================
#============= local library imports  ==========================
class PyScriptLexer(PythonLexer):
    def __init__(self, commands, **kw):
        self._extra_commands=commands.script_commands
        super(PyScriptLexer, self).__init__(**kw)

    def get_tokens_unprocessed(self, text):
        for index, token, value in PythonLexer.get_tokens_unprocessed(self, text):
            if token is Name and value in self._extra_commands:
                yield index, Name.Builtin, value
            else:
                yield index, token, value


#============= EOF =============================================

