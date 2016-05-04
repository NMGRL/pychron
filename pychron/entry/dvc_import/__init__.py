# ===============================================================================
# Copyright 2016 Jake Ross
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
from pychron.entry.dvc_import.model import DVCImporterModel
from pychron.entry.dvc_import.view import DVCImporterView
from pychron.envisage.view_util import open_view


def do_import_irradiation(dvc, sources, default_source=None):
    model = DVCImporterModel(dvc=dvc, sources=sources)

    model.source = next((k for k, v in sources.iteritems() if v == default_source), None)
    view = DVCImporterView(model=model)
    info = open_view(view)
    return info.result

# ============= EOF =============================================
