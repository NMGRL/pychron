# ===============================================================================
# Copyright 2014 Jake Ross
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
import os

from traits.api import Instance

#============= standard library imports ========================
#============= local library imports  ==========================
import yaml
from pychron.processing.export.destinations import YamlDestination
from pychron.processing.export.exporter import Exporter


class YamlAnalysisExporter(Exporter):
    destination = Instance(YamlDestination, ())

    def add(self, dbanalysis):
        self._ctx=dict()

    def export(self, *args, **kw):
        p=self.destination.destination
        if os.path.isdir(os.path.dirname(p)):
            with open(p, 'w') as fp:
                fp.write(yaml.dump(self._ctx, default_flow_style=False))
#============= EOF =============================================



