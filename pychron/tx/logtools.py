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
import io
import os
import sys
# ============= local library imports  ==========================
from twisted.logger import eventsFromJSONLogFile, textFileLogObserver


def print_log(path=None, output_stream=None):
    if path is None:
        from pychron.paths import paths
        path = os.path.join(paths.log_dir, 'pps.log.json')

    if output_stream is None:
        output_stream = sys.stdout
    elif isinstance(output_stream, (str, unicode)):
        output_stream = io.open(output_stream, 'w')

    output = textFileLogObserver(output_stream)
    for event in eventsFromJSONLogFile(io.open(path)):
        output(event)

# ============= EOF =============================================
